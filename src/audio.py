from __future__ import annotations

import asyncio
import io
import wave
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Any

from .diarization import analyze_chunk
from .events import event_publisher
from .logging_utils import get_logger
from .storage import blob_storage
from playwright.async_api import Page

logger = get_logger(__name__)


def _generate_silence_wav(duration_seconds: int = 30, sample_rate: int = 16000) -> bytes:
    """Generate a small silent WAV buffer as a placeholder for real audio capture."""
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
    meeting_id: str
    session_id: str
    stop_event: asyncio.Event
    page: Optional[Page] = None  # Page for real audio capture
    chunk_interval_seconds: int = 30
    chunk_counter: int = field(default=0, init=False)
    _audio_capture: Optional[Any] = field(default=None, init=False)

    async def run(self) -> None:
        """
        Loop capturing audio chunks every N seconds.
        
        Uses real audio capture if page is available, otherwise falls back to silent WAVs.
        """
        # Try to use real audio capture if page is available
        if self.page:
            try:
                from .audio_capture import AudioCapture
                self._audio_capture = AudioCapture(
                    page=self.page,
                    meeting_id=self.meeting_id,
                    session_id=self.session_id,
                    chunk_duration_seconds=self.chunk_interval_seconds,
                )
                await self._audio_capture.start()
                logger.info(
                    "Real audio capture initialized",
                    extra={
                        "extra_data": {
                            "meeting_id": self.meeting_id,
                            "session_id": self.session_id,
                        }
                    },
                )
            except Exception as e:
                logger.warning(
                    f"Could not start real audio capture, using fallback: {e}",
                    extra={
                        "extra_data": {
                            "meeting_id": self.meeting_id,
                            "session_id": self.session_id,
                        }
                    },
                )
                self._audio_capture = None
        while not self.stop_event.is_set():
            started_at = datetime.now(timezone.utc)
            timestamp_iso = started_at.isoformat()
            # Windows does not allow ':' in file names, so create a safe variant
            timestamp_safe = timestamp_iso.replace(":", "-")
            chunk_id = f"{self.session_id}-{self.chunk_counter}"
            blob_path = (
                f"{self.meeting_id}/{self.session_id}/{timestamp_safe}.wav"
            )

            # Try real audio capture first
            audio_bytes = None
            if self._audio_capture:
                try:
                    audio_bytes = await self._audio_capture.capture_chunk()
                    if audio_bytes:
                        # Validate audio chunk
                        import wave
                        import io
                        try:
                            wav_file = wave.open(io.BytesIO(audio_bytes), 'rb')
                            frames = wav_file.getnframes()
                            sample_rate = wav_file.getframerate()
                            duration = frames / sample_rate
                            wav_file.close()
                            
                            # Developer-level logging: Audio chunk metrics
                            chunk_size_kb = len(audio_bytes) / 1024
                            logger.info(
                                f"DEVELOPER: Audio chunk captured - {duration:.2f}s, {frames} frames, {sample_rate}Hz, {chunk_size_kb:.2f}KB",
                                extra={
                                    "extra_data": {
                                        "meeting_id": self.meeting_id,
                                        "session_id": self.session_id,
                                        "chunk_id": chunk_id,
                                        "duration_seconds": duration,
                                        "frames": frames,
                                        "sample_rate": sample_rate,
                                        "chunk_size_bytes": len(audio_bytes),
                                        "chunk_size_kb": chunk_size_kb,
                                        "chunk_number": self.chunk_counter,
                                    }
                                },
                            )
                            
                            # CRITICAL: Validate audio chunk quality
                            # Chunk must be at least 1 second of audio (not empty/corrupted)
                            min_duration_seconds = 1.0
                            if duration < min_duration_seconds:
                                logger.warning(
                                    f"DEVELOPER: Audio chunk too short ({duration:.2f}s < {min_duration_seconds}s) - marking as invalid",
                                    extra={
                                        "extra_data": {
                                            "meeting_id": self.meeting_id,
                                            "session_id": self.session_id,
                                            "chunk_id": chunk_id,
                                            "duration_seconds": duration,
                                            "min_duration_seconds": min_duration_seconds,
                                            "chunk_number": self.chunk_counter,
                                        }
                                    },
                                )
                                # Don't count this as a valid chunk
                                audio_bytes = None
                        except Exception as e:
                            logger.warning(
                                f"Could not validate audio chunk: {e}",
                                extra={
                                    "extra_data": {
                                        "meeting_id": self.meeting_id,
                                        "session_id": self.session_id,
                                        "chunk_id": chunk_id,
                                        "error": str(e),
                                    }
                                },
                            )
                except Exception as e:
                    logger.warning(f"Real audio capture failed: {e}")
            
            # Fallback to silent WAV if real capture failed or was invalid
            if not audio_bytes:
                audio_bytes = _generate_silence_wav(duration_seconds=self.chunk_interval_seconds)
                logger.info(
                    "DEVELOPER: Using fallback silent audio (real capture unavailable or invalid)",
                    extra={
                        "extra_data": {
                            "meeting_id": self.meeting_id,
                            "session_id": self.session_id,
                            "chunk_id": chunk_id,
                            "chunk_number": self.chunk_counter,
                            "fallback_reason": "real_capture_unavailable_or_invalid",
                            "note": "This chunk will be saved but may not contain real speech",
                        }
                    },
                )
                # Don't increment chunk counter for fallback chunks (they're not real audio)
                # But still save the file for consistency
            # Only count and save if we have valid audio bytes
            if audio_bytes:
                try:
                    # Save locally (and optionally to Azure)
                    local_path = await blob_storage.upload_bytes_with_retry(blob_path, audio_bytes)
                    
                    # Increment chunk counter only for valid chunks
                    self.chunk_counter += 1
                    
                    # Publish audio chunk event with local path
                    await event_publisher.publish_event(
                        "audio_chunk_created",
                        {
                            "chunk_id": chunk_id,
                            "meeting_id": self.meeting_id,
                            "session_id": self.session_id,
                            "local_path": local_path,
                            "blob_path": blob_path,  # Keep for backward compatibility
                            "timestamp": timestamp_iso,
                        },
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "Failed to save audio chunk",
                        extra={
                            "extra_data": {
                                "event": "audio_chunk_upload_failed",
                                "meeting_id": self.meeting_id,
                                "session_id": self.session_id,
                                "chunk_id": chunk_id,
                                "error": str(exc),
                            }
                        },
                    )
            else:

                # Run diarisation and publish active_speaker
                speakers = await analyze_chunk(
                    meeting_id=self.meeting_id,
                    session_id=self.session_id,
                    chunk_id=chunk_id,
                    audio_bytes=audio_bytes,
                )
                if speakers:
                    # Take top speaker as active for this chunk
                    top = max(speakers, key=lambda s: s.confidence)
                    await event_publisher.publish_event(
                        "active_speaker",
                        {
                            "chunk_id": chunk_id,
                            "meeting_id": self.meeting_id,
                            "session_id": self.session_id,
                            "speaker_label": top.label,
                            "confidence": top.confidence,
                            "timestamp": timestamp_iso,
                        },
                    )

            self.chunk_counter += 1
            try:
                await asyncio.wait_for(
                    self.stop_event.wait(), timeout=self.chunk_interval_seconds
                )
            except asyncio.TimeoutError:
                continue
        
        # Cleanup audio capture
        if self._audio_capture:
            try:
                await self._audio_capture.stop()
            except Exception:
                pass



