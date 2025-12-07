import asyncio
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from playwright.async_api import Page

from .audio import AudioCaptureLoop
from .config import get_settings
from .events import event_publisher
from .local_storage import get_local_storage
from .logging_utils import get_logger
from .meeting_flow.base import MeetingFlow
from .meeting_flow.gmeet import GoogleMeetFlow
from .meeting_flow.gmeet_enhanced import GoogleMeetFlowEnhanced
from .meeting_flow.teams import TeamsFlow
from .meeting_flow.teams_enhanced import TeamsFlowEnhanced
from .models import Platform, SessionStatus
from .playwright_client import PlaywrightManager
from .playwright_manager import get_enhanced_manager
from .google_auth.persistent_profile import get_profile_manager
from .participant_name_filter import is_valid_participant_name, clean_participant_name


logger = get_logger(__name__)


TEAMS_URL_RE = re.compile(r"https://teams\.microsoft\.com/.*", re.IGNORECASE)
GMEET_URL_RE = re.compile(r"https://meet\.google\.com/.*", re.IGNORECASE)


# ============================================================================
# BOT IDENTIFICATION CONFIGURATION
# ============================================================================

def get_bot_identifiers() -> List[str]:
    """
    Get all possible names that could identify the bot.
    
    This includes:
    1. bot_display_name from settings
    2. Google profile name (if using Google auth)
    3. Any custom names configured
    
    Returns lowercase list for case-insensitive matching.
    """
    settings = get_settings()
    identifiers = []
    
    # 1. Primary: bot_display_name from settings
    if hasattr(settings, 'bot_display_name') and settings.bot_display_name:
        identifiers.append(settings.bot_display_name.lower().strip())
    
    # 2. Google profile name - CRITICAL for Google profile login
    try:
        profile_manager = get_profile_manager()
        if profile_manager and hasattr(profile_manager, 'get_profile_name'):
            profile_name = profile_manager.get_profile_name()
            if profile_name:
                identifiers.append(profile_name.lower().strip())
    except Exception:
        pass
    
    # 3. Check environment variable for Google account name
    import os
    google_account_name = os.environ.get('GOOGLE_ACCOUNT_NAME', '').strip()
    if google_account_name:
        identifiers.append(google_account_name.lower())
    
    # 4. Check settings for additional bot names
    if hasattr(settings, 'bot_google_profile_name') and settings.bot_google_profile_name:
        identifiers.append(settings.bot_google_profile_name.lower().strip())
    
    # 5. Default fallback names
    default_names = ['meeting bot', 'meetingbot', 'bot']
    for name in default_names:
        if name not in identifiers:
            identifiers.append(name)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_identifiers = []
    for name in identifiers:
        if name and name not in seen:
            seen.add(name)
            unique_identifiers.append(name)
    
    return unique_identifiers


def is_bot_participant(participant: dict, bot_identifiers: List[str], detected_bot_name: str = None) -> bool:
    """
    Determine if a participant is the bot.
    
    Checks:
    1. is_bot flag from extractor (set when "(You)" detected)
    2. original_name contains "(You)" or "(you)"
    3. name matches any bot identifier (case-insensitive)
    4. name matches detected_bot_name from session
    
    Args:
        participant: Participant dict with 'name', 'original_name', 'is_bot' keys
        bot_identifiers: List of possible bot names (lowercase)
        detected_bot_name: Bot name detected during this session
    
    Returns:
        True if this participant is the bot
    """
    name = participant.get("name", "").strip()
    original_name = participant.get("original_name", name).strip()
    
    # Check 1: is_bot flag already set by extractor
    if participant.get("is_bot", False):
        return True
    
    # Check 2: "(You)" suffix in original name (case-insensitive)
    if original_name and "(you)" in original_name.lower():
        return True
    
    # Check 3: "(You)" suffix in name (case-insensitive)
    if name and "(you)" in name.lower():
        return True
    
    # Check 4: Match with detected bot name for this session
    if detected_bot_name:
        if name.lower() == detected_bot_name.lower():
            return True
    
    # Check 5: Exact match with bot identifiers
    name_lower = name.lower()
    if name_lower in bot_identifiers:
        return True
    
    # Check 6: Partial match - bot identifier is part of name or vice versa
    for identifier in bot_identifiers:
        if len(identifier) >= 3:
            if identifier in name_lower or name_lower in identifier:
                if len(identifier) >= len(name_lower) * 0.5 or len(name_lower) >= len(identifier) * 0.5:
                    return True
    
    return False


@dataclass
class MeetingSession:
    meeting_id: str
    platform: Platform
    meeting_url: str
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: SessionStatus = SessionStatus.created
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    error: Optional[str] = None
    last_participants: List[dict] = field(default_factory=list)
    audio_chunks: int = 0
    participants_history: Dict[str, Dict[str, Optional[str]]] = field(
        default_factory=dict
    )
    transcript: str = ""
    bot_name_detected: Optional[str] = None  # Store detected bot name for consistency


class SessionManager:
    def __init__(self) -> None:
        settings = get_settings()
        self._sessions: Dict[str, MeetingSession] = {}
        self._queue: "asyncio.Queue[MeetingSession]" = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(settings.max_concurrent_sessions)
        self._worker_task: Optional[asyncio.Task[None]] = None
        self._bot_identifiers: List[str] = get_bot_identifiers()
        
        logger.info(
            f"SessionManager initialized with bot identifiers: {self._bot_identifiers}",
            extra={"extra_data": {"bot_identifiers": self._bot_identifiers}}
        )

    async def start(self) -> None:
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._worker(), name="session-worker")
            logger.info(
                "SessionManager worker started",
                extra={"extra_data": {"component": "session_manager"}},
            )

    async def enqueue_session(
        self, meeting_id: str, platform: Platform, meeting_url: str
    ) -> MeetingSession:
        self._validate_meeting_url(platform, meeting_url)
        session = MeetingSession(meeting_id=meeting_id, platform=platform, meeting_url=meeting_url)
        self._sessions[session.session_id] = session
        await self._queue.put(session)

        await event_publisher.publish_event(
            "bot_joined",
            {
                "meeting_id": meeting_id,
                "platform": platform.value,
                "session_id": session.session_id,
                "timestamp": session.created_at.isoformat(),
            },
        )

        logger.info(
            "Session enqueued",
            extra={
                "extra_data": {
                    "event": "session_enqueued",
                    "meeting_id": meeting_id,
                    "platform": platform.value,
                    "session_id": session.session_id,
                    "timestamp": session.created_at.isoformat(),
                }
            },
        )
        return session

    def get_session(self, session_id: str) -> Optional[MeetingSession]:
        return self._sessions.get(session_id)

    def list_sessions(self) -> List[MeetingSession]:
        return list(self._sessions.values())

    def _validate_meeting_url(self, platform: Platform, meeting_url: str) -> None:
        if platform == Platform.teams and not TEAMS_URL_RE.match(meeting_url):
            raise ValueError("Invalid Teams meeting URL")
        if platform == Platform.gmeet and not GMEET_URL_RE.match(meeting_url):
            raise ValueError("Invalid Google Meet URL")

    async def _worker(self) -> None:
        while True:
            session = await self._queue.get()
            await self._semaphore.acquire()
            asyncio.create_task(self._run_session_wrapper(session))

    async def _run_session_wrapper(self, session: MeetingSession) -> None:
        try:
            await self._run_session(session)
        except Exception as exc:
            session.status = SessionStatus.failed
            session.error = str(exc)
            session.ended_at = datetime.now(timezone.utc)
            logger.error(
                "Session failed",
                extra={
                    "extra_data": {
                        "event": "session_failed",
                        "meeting_id": session.meeting_id,
                        "platform": session.platform.value,
                        "session_id": session.session_id,
                        "error": str(exc),
                    }
                },
            )
        finally:
            self._semaphore.release()

    def _create_flow(self, session: MeetingSession) -> MeetingFlow:
        if session.platform == Platform.teams:
            return TeamsFlowEnhanced(session.meeting_id, session.session_id)
        if session.platform == Platform.gmeet:
            return GoogleMeetFlowEnhanced(session.meeting_id, session.session_id)
        raise ValueError(f"Unsupported platform: {session.platform}")

    async def _run_session(self, session: MeetingSession) -> None:
        logger.info(
            "Session starting",
            extra={
                "extra_data": {
                    "event": "session_starting",
                    "meeting_id": session.meeting_id,
                    "platform": session.platform.value,
                    "session_id": session.session_id,
                }
            },
        )
        session.status = SessionStatus.joining
        session.started_at = datetime.now(timezone.utc)

        flow = self._create_flow(session)
        
        # Use enhanced playwright manager with per-session profiles
        settings = get_settings()
        use_enhanced = session.platform == Platform.gmeet and getattr(settings, 'google_login_required', False)
        
        if use_enhanced:
            enhanced_pw = await get_enhanced_manager()
            async with enhanced_pw.new_page_for_session(
                session.session_id, platform=session.platform.value
            ) as page:
                await flow.join_meeting(page, session.meeting_url)
                session.status = SessionStatus.in_meeting
                logger.info(
                    "Session joined meeting",
                    extra={
                        "extra_data": {
                            "event": "session_joined",
                            "meeting_id": session.meeting_id,
                            "platform": session.platform.value,
                            "session_id": session.session_id,
                        }
                    },
                )
                # Detect bot name after joining
                await self._detect_bot_name(session, flow, page)
                await self._run_session_loops(session, flow, page)
        else:
            # Fallback to original manager for Teams or if enhanced is disabled
            pw = await PlaywrightManager.get()
            async with pw.new_page(platform=session.platform.value) as page:
                await flow.join_meeting(page, session.meeting_url)
                session.status = SessionStatus.in_meeting
                logger.info(
                    "Session joined meeting",
                    extra={
                        "extra_data": {
                            "event": "session_joined",
                            "meeting_id": session.meeting_id,
                            "platform": session.platform.value,
                            "session_id": session.session_id,
                        }
                    },
                )
                # Detect bot name after joining
                await self._detect_bot_name(session, flow, page)
                await self._run_session_loops(session, flow, page)

    async def _detect_bot_name(self, session: MeetingSession, flow: MeetingFlow, page: Page) -> None:
        """
        Detect which participant is the bot on first extraction.
        
        This is called once after joining to establish the bot's name in this meeting.
        The bot is identified by the "(You)" suffix that Google Meet adds.
        """
        try:
            await asyncio.sleep(3)  # Wait for participant list to populate
            
            participants = await flow.read_participants(page)
            
            for p in participants:
                original_name = p.get("original_name", p.get("name", ""))
                
                # Check for "(You)" suffix - definitive bot indicator
                if "(you)" in original_name.lower():
                    # Extract clean name without "(You)"
                    clean_name = re.sub(r'\s*\(you\)\s*$', '', original_name, flags=re.IGNORECASE).strip()
                    session.bot_name_detected = clean_name
                    
                    # Add to bot identifiers if not already present
                    if clean_name.lower() not in self._bot_identifiers:
                        self._bot_identifiers.append(clean_name.lower())
                    
                    logger.info(
                        f"✅ BOT DETECTED: '{clean_name}' (from '{original_name}')",
                        extra={
                            "extra_data": {
                                "meeting_id": session.meeting_id,
                                "session_id": session.session_id,
                                "bot_name": clean_name,
                                "original_name": original_name,
                                "all_identifiers": self._bot_identifiers,
                            }
                        },
                    )
                    return
                
                # Check is_bot flag
                if p.get("is_bot", False):
                    clean_name = p.get("name", "").strip()
                    session.bot_name_detected = clean_name
                    
                    if clean_name.lower() not in self._bot_identifiers:
                        self._bot_identifiers.append(clean_name.lower())
                    
                    logger.info(
                        f"✅ BOT DETECTED (via is_bot flag): '{clean_name}'",
                        extra={
                            "extra_data": {
                                "meeting_id": session.meeting_id,
                                "session_id": session.session_id,
                                "bot_name": clean_name,
                            }
                        },
                    )
                    return
            
            logger.warning(
                "⚠️ Could not detect bot name from participants - using configured identifiers",
                extra={
                    "extra_data": {
                        "meeting_id": session.meeting_id,
                        "session_id": session.session_id,
                        "participants": [p.get("original_name", p.get("name")) for p in participants],
                        "bot_identifiers": self._bot_identifiers,
                    }
                },
            )
            
        except Exception as e:
            logger.warning(f"Error detecting bot name: {e}")

    async def _run_session_loops(self, session: MeetingSession, flow: MeetingFlow, page: Page) -> None:
        """Run audio capture and participant tracking loops for a session."""
        stop_event = asyncio.Event()
        audio_loop = AudioCaptureLoop(
            meeting_id=session.meeting_id,
            session_id=session.session_id,
            stop_event=stop_event,
            page=page,
        )
        
        # Initialize closed captions extractor
        from .closed_captions import ClosedCaptionsExtractor
        cc_extractor = ClosedCaptionsExtractor(platform=session.platform.value)

        async def participants_loop() -> None:
            while not stop_event.is_set():
                participants = await flow.read_participants(page)
                session.last_participants = participants

                # CRITICAL: Separate bot and real participants using improved identification
                real_participants = []
                bot_participants = []
                
                for p in participants:
                    name = p.get("name", "").strip()
                    if not name:
                        continue
                    
                    # CRITICAL: Validate it's a real participant name (not UI element)
                    if not is_valid_participant_name(name):
                        logger.debug(f"Filtering out invalid participant name: {name}")
                        continue
                    
                    # Use improved bot identification with session's detected bot name
                    if is_bot_participant(p, self._bot_identifiers, session.bot_name_detected):
                        bot_participants.append(p)
                        logger.debug(f"Identified as BOT: {name}")
                    else:
                        real_participants.append(p)
                        logger.debug(f"Identified as REAL USER: {name}")
                
                num_real_participants = len(real_participants)
                num_bot_participants = len(bot_participants)
                total_participants = len(participants)
                
                # Developer-level logging
                logger.info(
                    f"PARTICIPANT ANALYSIS - Total: {total_participants}, Real: {num_real_participants}, Bot: {num_bot_participants}",
                    extra={
                        "extra_data": {
                            "meeting_id": session.meeting_id,
                            "session_id": session.session_id,
                            "total_participants": total_participants,
                            "real_participants": num_real_participants,
                            "bot_participants": num_bot_participants,
                            "real_names": [p.get("name") for p in real_participants],
                            "bot_names": [p.get("name") for p in bot_participants],
                            "detected_bot_name": session.bot_name_detected,
                        }
                    },
                )

                # Update participants history (ALL participants including bot)
                current_time = datetime.now(timezone.utc).isoformat()
                
                # Save ALL participants (real + bot) with is_bot flag
                all_participants_to_save = real_participants + bot_participants
                
                for p in all_participants_to_save:
                    name = p.get("name", "Unknown")
                    if not name or name == "Unknown":
                        continue
                    
                    # Check if this is the bot
                    is_bot = is_bot_participant(p, self._bot_identifiers, session.bot_name_detected)
                    
                    if name not in session.participants_history:
                        session.participants_history[name] = {
                            "name": name,
                            "original_name": p.get("original_name", name),  # Preserve original name
                            "is_bot": is_bot,  # CRITICAL: Save is_bot flag
                            "join_time": current_time,
                            "leave_time": None,
                            "role": p.get("role", "guest"),
                        }
                    else:
                        # Update existing participant - ALWAYS update is_bot flag (may have changed)
                        session.participants_history[name]["is_bot"] = is_bot
                        # Update original_name if available
                        if "original_name" not in session.participants_history[name]:
                            session.participants_history[name]["original_name"] = p.get("original_name", name)
                        # Reset leave_time if they rejoined
                        if session.participants_history[name].get("leave_time"):
                            session.participants_history[name]["leave_time"] = None

                # Mark participants who left (check both real and bot)
                current_names = {p.get("name") for p in all_participants_to_save if p.get("name")}
                for name in session.participants_history:
                    if name not in current_names:
                        if session.participants_history[name].get("leave_time") is None:
                            session.participants_history[name]["leave_time"] = current_time

                # Publish participant update
                await event_publisher.publish_event(
                    "participant_update",
                    {
                        "meeting_id": session.meeting_id,
                        "session_id": session.session_id,
                        "participants": [p.get("name") for p in real_participants],
                        "real_count": num_real_participants,
                        "bot_count": num_bot_participants,
                        "total_count": total_participants,
                        "timestamp": current_time,
                    },
                )

                # Check if meeting is empty (only bot remains)
                should_leave = False
                
                # CRITICAL CHECK 1: If total participants > 1, stay
                if total_participants > 1:
                    logger.debug(f"STAYING: total_participants={total_participants} > 1")
                    should_leave = False
                # CRITICAL CHECK 2: If we have real participants, stay
                elif num_real_participants > 0:
                    logger.debug(f"STAYING: num_real_participants={num_real_participants} > 0")
                    should_leave = False
                # CRITICAL CHECK 3: Only consider leaving if no real participants
                else:
                    # Check if remaining participant is the bot
                    remaining_is_bot = False
                    if total_participants == 1:
                        remaining = participants[0]
                        remaining_is_bot = is_bot_participant(remaining, self._bot_identifiers, session.bot_name_detected)
                    
                    should_leave = (total_participants == 0 or (total_participants == 1 and remaining_is_bot))
                
                if should_leave:
                    logger.warning(
                        "⚠️ POTENTIAL EMPTY MEETING: Only bot detected - waiting 15 seconds to confirm",
                        extra={
                            "extra_data": {
                                "meeting_id": session.meeting_id,
                                "session_id": session.session_id,
                                "total_participants": total_participants,
                                "real_participants": num_real_participants,
                            }
                        },
                    )
                    
                    # Wait 15 seconds before leaving
                    await asyncio.sleep(15)
                    
                    # Verify again
                    participants_again = await flow.read_participants(page)
                    real_again = []
                    
                    for p in participants_again:
                        name = p.get("name", "").strip()
                        if not name or not is_valid_participant_name(name):
                            continue
                        if not is_bot_participant(p, self._bot_identifiers, session.bot_name_detected):
                            real_again.append(p)
                    
                    if len(real_again) > 0:
                        logger.info(f"✅ Found {len(real_again)} real participants after wait - staying in meeting")
                    else:
                        logger.info("Meeting is empty after 15 second wait - leaving")
                        stop_event.set()
                        break
                
                await asyncio.sleep(30)  # Check every 30 seconds

        async def audio_capture_loop() -> None:
            while not stop_event.is_set():
                try:
                    chunk_path = await audio_loop.capture_chunk()
                    if chunk_path:
                        session.audio_chunks += 1
                except Exception as e:
                    logger.error(f"Audio capture error: {e}")
                await asyncio.sleep(30)

        async def captions_loop() -> None:
            while not stop_event.is_set():
                try:
                    captions = await cc_extractor.extract_captions(page)
                    if captions:
                        session.transcript += captions + "\n"
                except Exception as e:
                    logger.debug(f"Captions extraction error: {e}")
                await asyncio.sleep(5)

        # Run all loops concurrently
        try:
            await asyncio.gather(
                participants_loop(),
                audio_capture_loop(),
                captions_loop(),
            )
        except asyncio.CancelledError:
            pass
        finally:
            stop_event.set()
            
            # Save session summary
            session.status = SessionStatus.ended
            session.ended_at = datetime.now(timezone.utc)
            
            await self._save_session_summary(session)

    async def _save_session_summary(self, session: MeetingSession) -> None:
        """Save session summary to local storage."""
        try:
            from .meeting_summary_builder import MeetingSummaryBuilder
            
            # Calculate duration
            duration_seconds = 0
            if session.started_at and session.ended_at:
                duration_seconds = int((session.ended_at - session.started_at).total_seconds())
            
            # Build proper summary using MeetingSummaryBuilder
            session_data = {
                "meeting_id": session.meeting_id,
                "session_id": session.session_id,
                "platform": session.platform.value,
                "meeting_url": session.meeting_url,
                "status": session.status.value,
                "created_at": session.created_at.isoformat(),
                "started_at": session.started_at.isoformat() if session.started_at else None,
                "ended_at": session.ended_at.isoformat() if session.ended_at else None,
                "error": session.error,
                "duration_seconds": duration_seconds,
                "transcript": session.transcript,
                "bot_name_detected": session.bot_name_detected,
            }
            
            summary = MeetingSummaryBuilder.build_summary(
                session_data=session_data,
                participants_history=session.participants_history,
                audio_chunks=session.audio_chunks,
                errors=[session.error] if session.error else None,
            )
            
            storage = get_local_storage()
            storage.save_session_data(session.session_id, summary)
            
            # Publish meeting summary event
            await event_publisher.publish_event(
                "meeting_summary",
                {
                    "meeting_id": session.meeting_id,
                    "session_id": session.session_id,
                    "summary": summary,
                },
            )
            
            logger.info(
                "Session summary saved",
                extra={
                    "extra_data": {
                        "meeting_id": session.meeting_id,
                        "session_id": session.session_id,
                        "bot_name_detected": session.bot_name_detected,
                    }
                },
            )
            
        except Exception as e:
            logger.error(f"Error saving session summary: {e}", exc_info=True)


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


# Export singleton instance for direct import
session_manager = get_session_manager()
