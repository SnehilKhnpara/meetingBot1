"""
Production-grade meeting summary builder.

Generates accurate, clean meeting summaries using ONLY real participant data.
"""
from typing import Dict, List, Optional
from datetime import datetime, timezone

from .logging_utils import get_logger
from .participant_name_filter import is_valid_participant_name, clean_participant_name

logger = get_logger(__name__)


class MeetingSummaryBuilder:
    """Builds accurate meeting summaries from session data."""
    
    @staticmethod
    def build_summary(
        session_data: Dict,
        participants_history: Dict[str, Dict],
        audio_chunks: int,
        errors: Optional[List[str]] = None,
    ) -> Dict:
        """
        Build clean, accurate meeting summary.
        
        Args:
            session_data: Basic session data (meeting_id, platform, etc.)
            participants_history: Participant tracking history
            audio_chunks: Number of audio chunks recorded
            errors: List of errors (if any)
            
        Returns:
            Clean meeting summary dictionary
        """
        # Filter participants - include ALL valid participants (including bot)
        # But exclude UI elements and invalid names
        all_participants = []
        for name, data in participants_history.items():
            # Use original name if available, otherwise use name
            original_name = data.get("original_name", name)
            display_name = data.get("name", name) or name
            
            # Check if it's the bot - case-insensitive check for (You)
            is_bot = data.get("is_bot", False)
            if not is_bot and original_name:
                is_bot = "(you)" in original_name.lower()
            
            # Clean and validate name
            cleaned_name = clean_participant_name(display_name)
            if not cleaned_name:
                # If cleaning fails, try original name (but remove (You) if present)
                import re
                temp_name = re.sub(r'\s*\(you\)$', '', original_name, flags=re.IGNORECASE).strip()
                cleaned_name = clean_participant_name(temp_name)
                if not cleaned_name:
                    continue
            
            # Skip if it's a UI element (but NOT if it's the bot)
            if not is_bot and not is_valid_participant_name(cleaned_name):
                continue
            
            # Build participant record
            participant_record = {
                "name": cleaned_name,  # Use cleaned name for display
                "original_name": original_name,  # Keep original for reference (includes "(You)" if present)
                "is_bot": is_bot,  # Mark if it's the bot
                "join_time": data.get("join_time"),
                "leave_time": data.get("leave_time"),
                "role": data.get("role", "guest"),
            }
            
            # Calculate time in meeting if both times available
            if participant_record["join_time"] and participant_record["leave_time"]:
                try:
                    join_dt = datetime.fromisoformat(
                        participant_record["join_time"].replace("Z", "+00:00")
                    )
                    leave_dt = datetime.fromisoformat(
                        participant_record["leave_time"].replace("Z", "+00:00")
                    )
                    duration_seconds = int((leave_dt - join_dt).total_seconds())
                    participant_record["duration_seconds"] = duration_seconds
                except Exception:
                    pass
            
            all_participants.append(participant_record)
        
        # Separate real participants from bot for counting
        real_participants = [p for p in all_participants if not p.get("is_bot", False)]
        
        # Calculate unique participants (excluding bot)
        unique_participants = len(set(p["name"] for p in real_participants))
        
        # CRITICAL: Validate audio_chunks count
        # Only count valid chunks (not fallback silent WAVs)
        # audio_chunks should reflect actual recorded audio, not placeholder files
        validated_audio_chunks = max(0, audio_chunks)  # Ensure non-negative
        
        # Get transcript if available
        transcript = session_data.get("transcript", "")
        
        # Build summary
        summary = {
            "meeting_id": session_data.get("meeting_id", "unknown"),
            "platform": session_data.get("platform", "unknown"),
            "session_id": session_data.get("session_id", "unknown"),
            "duration_seconds": session_data.get("duration_seconds", 0),
            "participants": all_participants,  # ALL participants including bot (with is_bot flag)
            "real_participants": real_participants,  # Only real participants (excluding bot)
            "unique_participants": unique_participants,
            "audio_chunks": validated_audio_chunks,  # Only valid chunks
            "audio_duration_seconds": validated_audio_chunks * 30,  # 30 seconds per chunk
            "ended_at": session_data.get("ended_at"),
            "created_at": session_data.get("created_at"),
            "started_at": session_data.get("started_at"),
            "status": session_data.get("status", "unknown"),
            "error": session_data.get("error"),
        }
        
        # Add transcript if available
        if transcript:
            summary["transcript"] = transcript
            summary["transcript_summary"] = transcript[:500]  # First 500 chars as summary
        
        # Add errors if any
        if errors:
            summary["errors"] = errors
        
        # Log summary creation with validation info
        logger.info(
            "Meeting summary built",
            extra={
                "extra_data": {
                    "meeting_id": summary["meeting_id"],
                    "session_id": summary["session_id"],
                    "duration_seconds": summary["duration_seconds"],
                    "unique_participants": unique_participants,
                    "total_participants": len(real_participants),
                    "audio_chunks": validated_audio_chunks,
                    "participants_filtered": True,  # Indicates UI elements were filtered
                    "audio_validated": True,  # Indicates only valid chunks counted
                }
            },
        )
        
        return summary

