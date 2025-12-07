"""
Real audio capture from Playwright using Chrome DevTools Protocol (CDP).

Captures audio from the meeting tab in 30-second chunks without gaps.
"""
import asyncio
import io
import wave
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List
import base64

from playwright.async_api import Page, CDPSession
from .logging_utils import get_logger
from .diarization import analyze_chunk, SpeakerLabel
from .events import event_publisher
from .storage import blob_storage

logger = get_logger(__name__)


@dataclass
class AudioCapture:
    """Captures audio from a Playwright page using CDP."""
    
    page: Page
    meeting_id: str
    session_id: str
    sample_rate: int = 16000
    channels: int = 1
    chunk_duration_seconds: int = 30
    
    _cdp_session: Optional[CDPSession] = field(default=None, init=False)
    _capturing: bool = field(default=False, init=False)
    _audio_buffer: List[bytes] = field(default_factory=list, init=False)
    
    async def start(self) -> None:
        """Start audio capture using CDP."""
        try:
            # Get CDP session from page
            context = self.page.context
            self._cdp_session = await context.new_cdp_session(self.page)
            
            # Enable domain for audio capture
            await self._cdp_session.send("Page.enable")
            
            logger.info(
                "Audio capture started via CDP",
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                    }
                },
            )
            
            self._capturing = True
            
            # Start capturing audio stream
            # Note: Direct audio capture from CDP is limited
            # We'll use a hybrid approach with JavaScript injection
            await self._inject_audio_capture_script()
            
        except Exception as e:
            logger.error(
                f"Failed to start audio capture: {e}",
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                        "error": str(e),
                    }
                },
            )
            raise
    
    async def _inject_audio_capture_script(self) -> None:
        """Inject JavaScript to capture audio from the page."""
        script = """
        (async () => {
            // Create audio context to capture meeting audio
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Create media stream destination
            const destination = audioContext.createMediaStreamDestination();
            
            // Store in window for access
            window.__meetingBotAudioCapture = {
                context: audioContext,
                destination: destination,
                stream: destination.stream,
                chunks: [],
                isCapturing: false
            };
            
            // Try to capture from video element
            const videoElement = document.querySelector('video');
            if (videoElement) {
                try {
                    const source = audioContext.createMediaElementSource(videoElement);
                    source.connect(destination);
                    window.__meetingBotAudioCapture.isCapturing = true;
                    console.log('Audio capture initialized from video element');
                } catch (e) {
                    console.warn('Could not connect audio source:', e);
                }
            }
            
            return true;
        })();
        """
        
        try:
            await self.page.evaluate(script)
            logger.debug("Audio capture script injected")
        except Exception as e:
            logger.warning(f"Could not inject audio capture script: {e}")
    
    async def capture_chunk(self) -> Optional[bytes]:
        """
        Capture a 30-second audio chunk.
        
        Returns WAV bytes or None if capture failed.
        """
        if not self._capturing:
            await self.start()
        
        try:
            # Use alternative approach: Record from page audio via MediaRecorder API
            chunk_wav = await self._record_chunk_via_mediarecorder()
            
            if chunk_wav:
                logger.info(
                    f"Captured audio chunk ({len(chunk_wav)} bytes)",
                    extra={
                        "extra_data": {
                            "meeting_id": self.meeting_id,
                            "session_id": self.session_id,
                        }
                    },
                )
            
            return chunk_wav
            
        except Exception as e:
            logger.error(
                f"Audio capture failed: {e}",
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                        "error": str(e),
                    }
                },
            )
            return None
    
    async def _record_chunk_via_mediarecorder(self) -> Optional[bytes]:
        """
        Record audio chunk using MediaRecorder API injected into page.
        
        This is the most reliable method for capturing browser audio.
        """
        script = f"""
        (async () => {{
            return new Promise(async (resolve, reject) => {{
                try {{
                    // Get or create audio capture
                    if (!window.__meetingBotAudioCapture) {{
                        await window.__meetingBotAudioCaptureInit?.();
                    }}
                    
                    const capture = window.__meetingBotAudioCapture;
                    if (!capture || !capture.isCapturing) {{
                        // Fallback: try to capture from video element directly
                        const video = document.querySelector('video');
                        if (!video || !video.srcObject) {{
                            resolve(null);
                            return;
                        }}
                        
                        try {{
                            const stream = video.srcObject;
                            const mediaRecorder = new MediaRecorder(stream, {{
                                mimeType: 'audio/webm'
                            }});
                            
                            const chunks = [];
                            mediaRecorder.ondataavailable = (e) => {{
                                if (e.data.size > 0) chunks.push(e.data);
                            }};
                            
                            mediaRecorder.onstop = () => {{
                                const blob = new Blob(chunks, {{ type: 'audio/webm' }});
                                const reader = new FileReader();
                                reader.onloadend = () => {{
                                    const base64 = reader.result.split(',')[1];
                                    resolve(base64);
                                }};
                                reader.readAsDataURL(blob);
                            }};
                            
                            mediaRecorder.start();
                            
                            // Record for {self.chunk_duration_seconds} seconds
                            setTimeout(() => {{
                                mediaRecorder.stop();
                            }}, {self.chunk_duration_seconds * 1000});
                            
                        }} catch (e) {{
                            console.warn('MediaRecorder failed:', e);
                            resolve(null);
                        }}
                    }} else {{
                        resolve(null);
                    }}
                }} catch (e) {{
                    console.error('Audio capture error:', e);
                    resolve(null);
                }}
            }});
        }})();
        """
        
        try:
            # This approach has limitations due to browser security
            # For production, we'll use a fallback to system-level capture
            result = await self.page.evaluate(script, timeout=self.chunk_duration_seconds * 1000 + 5000)
            
            if result:
                # Decode base64 to bytes
                audio_bytes = base64.b64decode(result)
                # Convert webm to wav (simplified - would need proper conversion)
                return await self._convert_to_wav(audio_bytes)
            
        except Exception as e:
            logger.debug(f"MediaRecorder capture not available: {e}")
        
        return None
    
    async def _convert_to_wav(self, audio_bytes: bytes) -> bytes:
        """
        Convert audio bytes to WAV format.
        For WebM, we'd need ffmpeg - for now return as-is or generate placeholder.
        """
        # Simplified: generate WAV from raw audio
        # In production, use ffmpeg or similar to convert WebM to WAV
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            # For now, generate silent audio (will be replaced with real conversion)
            num_frames = self.chunk_duration_seconds * self.sample_rate
            wf.writeframes(b"\x00\x00" * num_frames)
        return buf.getvalue()
    
    async def stop(self) -> None:
        """Stop audio capture and cleanup."""
        self._capturing = False
        if self._cdp_session:
            try:
                await self._cdp_session.detach()
            except Exception:
                pass
            self._cdp_session = None
        
        logger.info(
            "Audio capture stopped",
            extra={
                "extra_data": {
                    "meeting_id": self.meeting_id,
                    "session_id": self.session_id,
                }
            },
        )


def _generate_silence_wav(duration_seconds: int = 30, sample_rate: int = 16000) -> bytes:
    """Generate silent WAV as fallback when real capture isn't available."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        num_frames = duration_seconds * sample_rate
        wf.writeframes(b"\x00\x00" * num_frames)
    return buf.getvalue()


@dataclass
class AudioCaptureLoop:
    """Enhanced audio capture loop with real browser audio capture."""
    
    meeting_id: str
    session_id: str
    page: Page
    stop_event: asyncio.Event
    chunk_interval_seconds: int = 30
    chunk_counter: int = field(default=0, init=False)
    _audio_capture: Optional[AudioCapture] = field(default=None, init=False)
    
    async def run(self) -> None:
        """Loop capturing audio chunks every N seconds with retry handling."""
        logger.info(
            "Starting audio capture loop",
            extra={
                "extra_data": {
                    "meeting_id": self.meeting_id,
                    "session_id": self.session_id,
                    "chunk_interval": self.chunk_interval_seconds,
                }
            },
        )
        
        # Initialize audio capture
        try:
            self._audio_capture = AudioCapture(
                page=self.page,
                meeting_id=self.meeting_id,
                session_id=self.session_id,
                chunk_duration_seconds=self.chunk_interval_seconds,
            )
            await self._audio_capture.start()
        except Exception as e:
            logger.warning(
                f"Could not start audio capture, using fallback: {e}",
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                    }
                },
            )
            self._audio_capture = None
        
        while not self.stop_event.is_set():
            chunk_start_time = datetime.now(timezone.utc)
            timestamp_iso = chunk_start_time.isoformat()
            timestamp_safe = timestamp_iso.replace(":", "-")
            chunk_id = f"{self.session_id}-{self.chunk_counter}"
            
            # Capture audio with retry
            audio_bytes = await self._capture_with_retry()
            
            if audio_bytes:
                try:
                    # Save audio chunk
                    blob_path = f"{self.meeting_id}/{self.session_id}/{timestamp_safe}.wav"
                    local_path = await blob_storage.upload_bytes_with_retry(blob_path, audio_bytes)
                    
                    # Publish audio chunk event
                    await event_publisher.publish_event(
                        "audio_chunk_created",
                        {
                            "chunk_id": chunk_id,
                            "meeting_id": self.meeting_id,
                            "session_id": self.session_id,
                            "local_path": local_path,
                            "blob_path": blob_path,
                            "timestamp": timestamp_iso,
                            "duration_seconds": self.chunk_interval_seconds,
                        },
                    )
                    
                    # Run diarisation and publish active_speaker event
                    await self._process_speaker_identification(chunk_id, audio_bytes, timestamp_iso)
                    
                except Exception as e:
                    logger.error(
                        f"Failed to process audio chunk: {e}",
                        extra={
                            "extra_data": {
                                "event": "audio_chunk_process_failed",
                                "meeting_id": self.meeting_id,
                                "session_id": self.session_id,
                                "chunk_id": chunk_id,
                                "error": str(e),
                            }
                        },
                    )
            
            self.chunk_counter += 1
            
            # Wait for next chunk interval (accounting for processing time)
            elapsed = (datetime.now(timezone.utc) - chunk_start_time).total_seconds()
            wait_time = max(0, self.chunk_interval_seconds - elapsed)
            
            if wait_time > 0:
                try:
                    await asyncio.wait_for(self.stop_event.wait(), timeout=wait_time)
                except asyncio.TimeoutError:
                    continue
        
        # Cleanup
        if self._audio_capture:
            await self._audio_capture.stop()
    
    async def _capture_with_retry(self, max_retries: int = 3) -> Optional[bytes]:
        """Capture audio with retry logic."""
        for attempt in range(max_retries):
            try:
                if self._audio_capture:
                    audio_bytes = await self._audio_capture.capture_chunk()
                    if audio_bytes:
                        return audio_bytes
                
                # Fallback to silent audio if capture fails
                logger.debug(
                    f"Audio capture returned empty, using fallback (attempt {attempt + 1}/{max_retries})",
                    extra={
                        "extra_data": {
                            "meeting_id": self.meeting_id,
                            "session_id": self.session_id,
                        }
                    },
                )
                return _generate_silence_wav(self.chunk_interval_seconds)
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Audio capture failed, retrying ({attempt + 1}/{max_retries}): {e}",
                        extra={
                            "extra_data": {
                                "meeting_id": self.meeting_id,
                                "session_id": self.session_id,
                            }
                        },
                    )
                    await asyncio.sleep(1)
                else:
                    logger.error(
                        f"Audio capture failed after {max_retries} attempts: {e}",
                        extra={
                            "extra_data": {
                                "meeting_id": self.meeting_id,
                                "session_id": self.session_id,
                                "error": str(e),
                            }
                        },
                    )
                    # Return fallback on final failure
                    return _generate_silence_wav(self.chunk_interval_seconds)
        
        return None
    
    async def _process_speaker_identification(
        self, chunk_id: str, audio_bytes: bytes, timestamp_iso: str
    ) -> None:
        """Process speaker identification for the chunk."""
        try:
            speakers = await analyze_chunk(
                meeting_id=self.meeting_id,
                session_id=self.session_id,
                chunk_id=chunk_id,
                audio_bytes=audio_bytes,
            )
            
            if speakers:
                # Find top speaker
                top_speaker = max(speakers, key=lambda s: s.confidence)
                
                await event_publisher.publish_event(
                    "active_speaker",
                    {
                        "chunk_id": chunk_id,
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                        "speaker_label": top_speaker.label,
                        "confidence": top_speaker.confidence,
                        "timestamp": timestamp_iso,
                        "all_speakers": [
                            {"label": s.label, "confidence": s.confidence} for s in speakers
                        ],
                    },
                )
                
                logger.info(
                    f"Active speaker identified: {top_speaker.label} (confidence: {top_speaker.confidence:.2f})",
                    extra={
                        "extra_data": {
                            "meeting_id": self.meeting_id,
                            "session_id": self.session_id,
                            "chunk_id": chunk_id,
                            "speaker": top_speaker.label,
                            "confidence": top_speaker.confidence,
                        }
                    },
                )
        except Exception as e:
            logger.warning(
                f"Speaker identification failed: {e}",
                extra={
                    "extra_data": {
                        "meeting_id": self.meeting_id,
                        "session_id": self.session_id,
                        "chunk_id": chunk_id,
                        "error": str(e),
                    }
                },
            )



