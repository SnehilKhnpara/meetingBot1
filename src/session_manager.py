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


logger = get_logger(__name__)


TEAMS_URL_RE = re.compile(r"https://teams\.microsoft\.com/.*", re.IGNORECASE)
GMEET_URL_RE = re.compile(r"https://meet\.google\.com/.*", re.IGNORECASE)


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
    transcript: str = ""  # Closed captions transcript


class SessionManager:
    def __init__(self) -> None:
        settings = get_settings()
        self._sessions: Dict[str, MeetingSession] = {}
        self._queue: "asyncio.Queue[MeetingSession]" = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(settings.max_concurrent_sessions)
        self._worker_task: Optional[asyncio.Task[None]] = None

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
        except Exception as exc:  # noqa: BLE001
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
            # Use enhanced flow for production-grade features
            return TeamsFlowEnhanced(session.meeting_id, session.session_id)
        if session.platform == Platform.gmeet:
            # Use enhanced flow for production-grade join logic
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
        use_enhanced = session.platform == Platform.gmeet and settings.google_login_required
        
        if use_enhanced:
            enhanced_pw = await get_enhanced_manager()
            async with enhanced_pw.new_page_for_session(
                session.session_id, platform=session.platform.value
            ) as page:  # type: Page
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
                await self._run_session_loops(session, flow, page)
        else:
            # Fallback to original manager for Teams or if enhanced is disabled
            pw = await PlaywrightManager.get()
            async with pw.new_page(platform=session.platform.value) as page:  # type: Page
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
                await self._run_session_loops(session, flow, page)
    
    async def _run_session_loops(self, session: MeetingSession, flow: MeetingFlow, page: Page) -> None:
        """Run audio capture and participant tracking loops for a session."""
        stop_event = asyncio.Event()
        audio_loop = AudioCaptureLoop(
            meeting_id=session.meeting_id,
            session_id=session.session_id,
            stop_event=stop_event,
            page=page,  # Pass page for real audio capture
        )
        
        # Initialize closed captions extractor
        from .closed_captions import ClosedCaptionsExtractor
        cc_extractor = ClosedCaptionsExtractor(platform=session.platform.value)

        async def participants_loop() -> None:
                while not stop_event.is_set():
                    # CRITICAL: Use multiple methods to extract participants for accuracy
                    participants = await flow.read_participants(page)
                    session.last_participants = participants

                    # CRITICAL FIX: Count ALL participants (robust extractor already filters UI elements)
                    # The robust extractor handles filtering, so we just need to separate bot from real users
                    real_participants = []
                    bot_participants = []
                    
                    # Simple separation: bot has "(You)" suffix or matches bot_display_name
                    from .config import get_settings
                    settings = get_settings()
                    bot_display_name = settings.bot_display_name
                    
                    for p in participants:
                        name = p.get("name", "").strip()
                        if not name:
                            continue
                        
                        # Check if it's the bot - use is_bot flag from extractor OR check name
                        is_bot = p.get("is_bot", False)  # Robust extractor sets this
                        if not is_bot:
                            # Fallback checks: original name had "(You)" (case-insensitive) or matches bot name
                            original_name = p.get("original_name", name)
                            # Case-insensitive check for (You)
                            if original_name and "(you)" in original_name.lower():
                                is_bot = True
                            elif name.lower() == bot_display_name.lower():
                                is_bot = True
                        
                        if is_bot:
                            bot_participants.append(p)
                        else:
                            # Everything else is a real participant (robust extractor already filtered UI)
                            real_participants.append(p)
                    
                    # CRITICAL ANALYSIS: Multiple checks before deciding to leave
                    from .config import get_settings
                    settings = get_settings()
                    bot_display_name = settings.bot_display_name
                    
                    num_real_participants = len(real_participants)
                    num_bot_participants = len(bot_participants)
                    total_participants = len(participants)
                    
                    # Developer-level logging: Show detailed analysis
                    logger.info(
                        f"DEVELOPER: Participant analysis - Total: {total_participants}, Real: {num_real_participants}, Bot: {num_bot_participants}",
                        extra={
                            "extra_data": {
                                "meeting_id": session.meeting_id,
                                "session_id": session.session_id,
                                "total_participants": total_participants,
                                "real_participants": num_real_participants,
                                "bot_participants": num_bot_participants,
                                "all_participants": [p.get("name") for p in participants],
                                "real_participant_names": [p.get("name") for p in real_participants],
                                "bot_participant_names": [p.get("name") for p in bot_participants],
                            }
                        },
                    )
                    
                    # CRITICAL CHECK 1: If total_participants > 1, there MUST be at least one real user
                    # This is the PRIMARY check - if there are 2+ participants, stay in meeting
                    if total_participants > 1:
                        # There's at least one other participant - don't leave
                        logger.info(
                            f"✅ STAYING: Meeting has {total_participants} total participants - at least one other person is present",
                            extra={
                                "extra_data": {
                                    "meeting_id": session.meeting_id,
                                    "session_id": session.session_id,
                                    "total_participants": total_participants,
                                    "real_participants": num_real_participants,
                                    "all_participants": [p.get("name") for p in participants],
                                    "decision": "stay_in_meeting",
                                    "reason": "total_participants_gt_1",
                                }
                            },
                        )
                        should_leave = False
                    # CRITICAL CHECK 2: If we have real participants (even if total is 1), stay
                    elif num_real_participants > 0:
                        logger.info(
                            f"✅ STAYING: Found {num_real_participants} real participant(s) - staying in meeting",
                            extra={
                                "extra_data": {
                                    "meeting_id": session.meeting_id,
                                    "session_id": session.session_id,
                                    "real_participants": num_real_participants,
                                    "real_participant_names": [p.get("name") for p in real_participants],
                                    "decision": "stay_in_meeting",
                                    "reason": "real_participants_gt_0",
                                }
                            },
                        )
                        should_leave = False
                    # CRITICAL CHECK 3: Only consider leaving if total <= 1 AND no real participants
                    else:
                        # Check if remaining participant is the bot
                        remaining_is_bot = False
                        if total_participants == 1:
                            remaining_name = participants[0].get("name", "").strip()
                            # Check if it's "(You)" or matches bot_display_name
                            if "(You)" in remaining_name:
                                remaining_is_bot = True
                            else:
                                cleaned_remaining = clean_participant_name(remaining_name)
                                if cleaned_remaining and cleaned_remaining.lower() == bot_display_name.lower():
                                    remaining_is_bot = True
                        
                        # Only leave if: no real participants AND (empty OR only bot)
                        should_leave = (
                            num_real_participants == 0  # No real participants
                            and (total_participants == 0 or (total_participants == 1 and remaining_is_bot))  # Only bot/user or empty
                        )
                    
                    # CRITICAL: Only proceed with 15-second wait if ALL checks pass
                    if should_leave:
                        logger.warning(
                            "⚠️ POTENTIAL EMPTY MEETING: Only bot/user detected - performing detailed verification",
                            extra={
                                "extra_data": {
                                    "meeting_id": session.meeting_id,
                                    "session_id": session.session_id,
                                    "total_participants": total_participants,
                                    "real_participants": num_real_participants,
                                    "bot_participants": num_bot_participants,
                                    "all_participants": [p.get("name") for p in participants],
                                    "analysis": "starting_verification",
                                }
                            },
                        )
                        
                        # CRITICAL: Perform multiple verification checks BEFORE waiting 15 seconds
                        # Check 1: Verify participant extraction is working
                        verification_passed = True
                        verification_checks = []
                        
                        # Check 1: Re-extract participants immediately (no wait)
                        participants_check1 = await flow.read_participants(page)
                        total_check1 = len(participants_check1)
                        real_check1 = [p for p in participants_check1 if "(You)" not in p.get("name", "")]
                        num_real_check1 = len(real_check1)
                        
                        verification_checks.append({
                            "check": "immediate_recheck",
                            "total": total_check1,
                            "real": num_real_check1,
                            "passed": total_check1 > 1 or num_real_check1 > 0,
                        })
                        
                        if total_check1 > 1 or num_real_check1 > 0:
                            logger.info(
                                "✅ VERIFICATION PASSED: Found participants on immediate recheck - staying in meeting",
                                extra={
                                    "extra_data": {
                                        "meeting_id": session.meeting_id,
                                        "session_id": session.session_id,
                                        "total_check1": total_check1,
                                        "real_check1": num_real_check1,
                                        "decision": "stay_in_meeting",
                                        "reason": "participants_found_on_recheck",
                                    }
                                },
                            )
                            verification_passed = False
                            should_leave = False
                        
                        # Only proceed with 15-second wait if verification still indicates empty
                        if verification_passed and should_leave:
                            logger.info(
                                "⏳ WAITING 15 SECONDS: Performing final verification before leaving",
                                extra={
                                    "extra_data": {
                                        "meeting_id": session.meeting_id,
                                        "session_id": session.session_id,
                                        "verification_checks": verification_checks,
                                        "wait_reason": "final_confirmation",
                                    }
                                },
                            )
                            
                            # BOSS ORDER: Wait exactly 15 seconds to confirm
                            await asyncio.sleep(15)
                            
                            # CRITICAL: Verify again with same filtering logic
                            participants_again = await flow.read_participants(page)
                            real_participants_again = []
                            bot_participants_again = []
                            
                            for p in participants_again:
                                name = p.get("name", "").strip()
                                if not name:
                                    continue
                                is_bot = "(You)" in name
                                if is_bot:
                                    bot_participants_again.append(p)
                                    continue
                                
                                # Check for UI elements
                                is_ui_element = False
                                if name:
                                    name_lower = name.lower()
                                    ui_patterns = [
                                        "backgrounds and effects",
                                        "you can't unmute",
                                        "your microphone is off",
                                        "your camera is off",
                                        "settings",
                                        "more options",
                                    ]
                                    for pattern in ui_patterns:
                                        if pattern in name_lower:
                                            is_ui_element = True
                                            break
                                
                                if not is_ui_element:
                                    real_participants_again.append(p)
                            
                            num_real_again = len(real_participants_again)
                            num_bot_again = len(bot_participants_again)
                            total_again = len(participants_again)
                            
                            logger.info(
                                f"DEVELOPER: Final verification after 15s - Total: {total_again}, Real: {num_real_again}, Bot: {num_bot_again}",
                                extra={
                                    "extra_data": {
                                        "meeting_id": session.meeting_id,
                                        "session_id": session.session_id,
                                        "total_again": total_again,
                                        "real_again": num_real_again,
                                        "bot_again": num_bot_again,
                                        "all_participants_again": [p.get("name") for p in participants_again],
                                        "real_participants_again": [p.get("name") for p in real_participants_again],
                                    }
                                },
                            )
                            
                            # Check if remaining participant is the bot
                            remaining_is_bot_again = False
                            if total_again == 1:
                                remaining_name_again = participants_again[0].get("name", "").strip()
                                if "(You)" in remaining_name_again:
                                    remaining_is_bot_again = True
                                else:
                                    cleaned_remaining_again = clean_participant_name(remaining_name_again)
                                    if cleaned_remaining_again and cleaned_remaining_again.lower() == bot_display_name.lower():
                                        remaining_is_bot_again = True
                            
                            # CRITICAL: Only leave if STILL no real participants AND remaining is bot
                            # AND total is still <= 1
                            final_should_leave = (
                                total_again <= 1  # Still only bot or empty
                                and num_real_again == 0  # Still no real participants
                                and (total_again == 0 or (total_again == 1 and remaining_is_bot_again))  # Only bot or empty
                            )
                            
                            if final_should_leave:
                                logger.info(
                                    "✅ CONFIRMED EMPTY: NO REAL PARTICIPANTS after 15 seconds - leaving NOW",
                                    extra={
                                        "extra_data": {
                                            "meeting_id": session.meeting_id,
                                            "session_id": session.session_id,
                                            "wait_time_seconds": 15,
                                            "final_real_participants": num_real_again,
                                            "final_total": total_again,
                                            "final_bot_participants": num_bot_again,
                                            "verification": "passed",
                                            "all_checks": verification_checks,
                                        }
                                    },
                                )
                            else:
                                # Found participants during wait - stay in meeting
                                logger.info(
                                    "✅ PARTICIPANTS FOUND: Real participants detected during 15s wait - staying in meeting",
                                    extra={
                                        "extra_data": {
                                            "meeting_id": session.meeting_id,
                                            "session_id": session.session_id,
                                            "final_real_participants": num_real_again,
                                            "final_total": total_again,
                                            "decision": "stay_in_meeting",
                                            "reason": "participants_found_during_wait",
                                        }
                                    },
                                )
                                should_leave = False
                                final_should_leave = False
                            
                            if final_should_leave:
                                # BOSS ORDER: Leave the meeting immediately
                                try:
                                    # Try to leave using the flow's leave method if available
                                    if hasattr(flow, 'leave_meeting'):
                                        await flow.leave_meeting(page)
                                    else:
                                        # Use MeetingEndDetector to leave
                                        from .meeting_end_detector import MeetingEndDetector
                                        detector = MeetingEndDetector(
                                            platform=session.platform.value,
                                            meeting_id=session.meeting_id,
                                            session_id=session.session_id
                                        )
                                        await detector.leave_meeting_cleanly(page)
                                        logger.info(
                                            "Successfully clicked Leave button (BOSS ORDER)",
                                            extra={
                                                "extra_data": {
                                                    "meeting_id": session.meeting_id,
                                                    "session_id": session.session_id,
                                                }
                                            },
                                        )
                                except Exception as e:
                                    logger.error(
                                        f"Error leaving meeting: {e}",
                                        extra={
                                            "extra_data": {
                                                "meeting_id": session.meeting_id,
                                                "session_id": session.session_id,
                                                "error": str(e),
                                            }
                                        },
                                    )
                                # Stop the loop
                                stop_event.set()
                                break

                    # Developer-level logging: Participant update cycle
                    logger.debug(
                        f"DEVELOPER: Participant update cycle - {len(participants)} total, {len(real_participants)} real",
                        extra={
                            "extra_data": {
                                "meeting_id": session.meeting_id,
                                "session_id": session.session_id,
                                "total_participants": len(participants),
                                "real_participants": len(real_participants),
                                "participant_names": [p.get("name") for p in participants],
                                "real_participant_names": [p.get("name") for p in real_participants],
                            }
                        },
                    )
                    
                    # Update join/leave times (include all participants including bot/user)
                    now_iso = datetime.now(timezone.utc).isoformat()
                    current_names = {p.get("name") for p in participants if p.get("name")}
                    # Mark joins
                    for p in participants:
                        name = p.get("name", "").strip()
                        if not name:
                            continue
                        
                        if name not in session.participants_history:
                            session.participants_history[name] = {
                                "name": name,
                                "original_name": p.get("original_name", name),  # Keep original name
                                "is_bot": p.get("is_bot", False),  # Mark if it's the bot
                                "join_time": now_iso,
                                "leave_time": None,
                                "role": p.get("role", "guest"),
                            }
                        else:
                            # Keep existing join_time; update leave_time back to None if they rejoined
                            session.participants_history[name]["leave_time"] = None
                            # Update is_bot flag if available
                            if "is_bot" in p:
                                session.participants_history[name]["is_bot"] = p.get("is_bot", False)
                            if "original_name" in p:
                                session.participants_history[name]["original_name"] = p.get("original_name", name)
                    # Mark leaves
                    for name, rec in session.participants_history.items():
                        if name not in current_names and rec.get("leave_time") is None:
                            rec["leave_time"] = now_iso

                    await event_publisher.publish_event(
                        "participant_update",
                        {
                            "meeting_id": session.meeting_id,
                            "session_id": session.session_id,
                            "participants": list(session.participants_history.values()),
                            "other_participants_count": len(other_participants),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                    )
                    try:
                        await asyncio.wait_for(stop_event.wait(), timeout=30)
                    except asyncio.TimeoutError:
                        continue

        audio_task = asyncio.create_task(audio_loop.run())
        participants_task = asyncio.create_task(participants_loop())

        await flow.wait_for_meeting_end(page)
        stop_event.set()
        await asyncio.gather(audio_task, participants_task, return_exceptions=True)

        session.audio_chunks = audio_loop.chunk_counter
        
        session.status = SessionStatus.ended
        session.ended_at = datetime.now(timezone.utc)
        logger.info(
            "Session ended",
            extra={
                "extra_data": {
                    "event": "session_ended",
                    "meeting_id": session.meeting_id,
                    "platform": session.platform.value,
                    "session_id": session.session_id,
                }
            },
        )

        # Publish meeting summary
        duration_seconds = 0
        if session.started_at and session.ended_at:
            duration_seconds = int(
                (session.ended_at - session.started_at).total_seconds()
            )

        # Build accurate summary using MeetingSummaryBuilder
        from .meeting_summary_builder import MeetingSummaryBuilder
        
        summary_data = MeetingSummaryBuilder.build_summary(
            session_data={
                "meeting_id": session.meeting_id,
                "platform": session.platform.value,
                "session_id": session.session_id,
                "duration_seconds": duration_seconds,
                "ended_at": session.ended_at.isoformat() if session.ended_at else None,
                "created_at": session.created_at.isoformat(),
                "started_at": session.started_at.isoformat() if session.started_at else None,
                "status": session.status.value,
                "error": session.error,
                "transcript": session.transcript or '',  # Include transcript if available
            },
            participants_history=session.participants_history,
            audio_chunks=session.audio_chunks,
            errors=[session.error] if session.error else None,
        )
        
        await event_publisher.publish_event("meeting_summary", summary_data)
        
        # Save session data locally
        local_storage = get_local_storage()
        local_storage.save_session_data(session.session_id, summary_data)


session_manager = SessionManager()



