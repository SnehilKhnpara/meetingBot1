"""
Debug helpers for testing and validating meeting bot functionality.

Use these functions to test participant extraction, meeting end detection, and audio validation.
"""
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional

from playwright.async_api import Page, async_playwright

from .config import get_settings
from .participant_extractor import ParticipantExtractor
from .participant_name_filter import is_valid_participant_name, clean_participant_name
from .meeting_end_detector import MeetingEndDetector
from .logging_utils import get_logger

logger = get_logger(__name__)


async def test_participant_extraction(page: Page, platform: str = "gmeet") -> Dict:
    """
    Test participant extraction and show what was filtered.
    
    Returns:
        Dict with raw names, filtered names, and validation results
    """
    extractor = ParticipantExtractor(platform=platform)
    participants = await extractor.extract_participants(page)
    
    # Get raw names for comparison
    raw_names = []
    try:
        if platform == "gmeet":
            elements = await page.query_selector_all('[data-self-name]')
            for el in elements:
                name = await el.get_attribute("data-self-name")
                if name:
                    raw_names.append(name)
    except Exception:
        pass
    
    # Validate each name
    validation_results = []
    for name in raw_names:
        is_valid = is_valid_participant_name(name)
        cleaned = clean_participant_name(name)
        validation_results.append({
            "raw_name": name,
            "is_valid": is_valid,
            "cleaned": cleaned,
            "reason": "valid" if is_valid else "filtered_out",
        })
    
    return {
        "platform": platform,
        "raw_names": raw_names,
        "raw_count": len(raw_names),
        "extracted_participants": [p.get("name") for p in participants],
        "extracted_count": len(participants),
        "validation_results": validation_results,
    }


async def test_meeting_end_detection(
    page: Page,
    platform: str,
    meeting_id: str,
    session_id: str,
) -> Dict:
    """
    Test meeting end detection logic.
    
    Returns:
        Dict with detection results and reasoning
    """
    detector = MeetingEndDetector(
        platform=platform,
        meeting_id=meeting_id,
        session_id=session_id,
    )
    
    is_empty = await detector._check_meeting_empty(page)
    
    # Get participant count for context
    extractor = ParticipantExtractor(platform=platform)
    participants = await extractor.extract_participants(page)
    
    real_participants = []
    for p in participants:
        name = p.get("name", "").strip()
        if not name:
            continue
        is_bot = "(You)" in name
        if is_bot:
            name = name.replace("(You)", "").strip()
        cleaned = clean_participant_name(name)
        if cleaned and not is_bot:
            real_participants.append(p)
    
    settings = get_settings()
    
    return {
        "is_empty": is_empty,
        "total_participants": len(participants),
        "real_participants": len(real_participants),
        "bot_display_name": settings.bot_display_name,
        "participant_names": [p.get("name") for p in participants],
        "real_participant_names": [p.get("name") for p in real_participants],
        "should_leave": is_empty,
    }


async def validate_audio_chunk(audio_bytes: bytes) -> Dict:
    """
    Validate an audio chunk and return metrics.
    
    Returns:
        Dict with validation results
    """
    import wave
    import io
    
    try:
        wav_file = wave.open(io.BytesIO(audio_bytes), 'rb')
        frames = wav_file.getnframes()
        sample_rate = wav_file.getframerate()
        channels = wav_file.getnchannels()
        duration = frames / sample_rate
        wav_file.close()
        
        chunk_size_bytes = len(audio_bytes)
        chunk_size_kb = chunk_size_bytes / 1024
        
        # Validation
        min_duration_seconds = 1.0
        is_valid = duration >= min_duration_seconds
        
        return {
            "is_valid": is_valid,
            "duration_seconds": duration,
            "frames": frames,
            "sample_rate": sample_rate,
            "channels": channels,
            "chunk_size_bytes": chunk_size_bytes,
            "chunk_size_kb": chunk_size_kb,
            "min_duration_seconds": min_duration_seconds,
            "validation_passed": is_valid,
        }
    except Exception as e:
        return {
            "is_valid": False,
            "error": str(e),
            "validation_passed": False,
        }


def analyze_session_summary(session_file: Path) -> Dict:
    """
    Analyze a session summary JSON file and validate its accuracy.
    
    Returns:
        Dict with validation results
    """
    with open(session_file, 'r') as f:
        summary = json.load(f)
    
    issues = []
    warnings = []
    
    # Check participants
    participants = summary.get("participants", [])
    for p in participants:
        name = p.get("name", "")
        if not is_valid_participant_name(name):
            issues.append(f"Invalid participant name: {name}")
    
    # Check audio chunks
    audio_chunks = summary.get("audio_chunks", 0)
    duration_seconds = summary.get("duration_seconds", 0)
    expected_chunks = max(1, duration_seconds // 30)
    
    if audio_chunks > expected_chunks * 2:
        warnings.append(f"Audio chunks ({audio_chunks}) seems high for duration ({duration_seconds}s)")
    
    # Check participant count
    if len(participants) == 0 and duration_seconds > 60:
        warnings.append("No participants but meeting lasted > 1 minute - might be missing data")
    
    return {
        "session_id": summary.get("session_id"),
        "meeting_id": summary.get("meeting_id"),
        "issues": issues,
        "warnings": warnings,
        "participants_count": len(participants),
        "audio_chunks": audio_chunks,
        "duration_seconds": duration_seconds,
        "is_valid": len(issues) == 0,
    }


async def debug_meeting_state(page: Page, platform: str = "gmeet") -> Dict:
    """
    Comprehensive debug function to check current meeting state.
    
    Returns:
        Dict with all relevant state information
    """
    extractor = ParticipantExtractor(platform=platform)
    participants = await extractor.extract_participants(page)
    
    # Get page content for analysis
    content = await page.content()
    
    # Check for empty meeting indicators
    content_lower = content.lower()
    empty_indicators = [
        "you're the only one",
        "you are the only one",
        "waiting for others",
        "no one else is here",
    ]
    found_indicators = [ind for ind in empty_indicators if ind in content_lower]
    
    # Count real participants
    real_participants = []
    for p in participants:
        name = p.get("name", "").strip()
        if not name:
            continue
        is_bot = "(You)" in name
        if is_bot:
            name = name.replace("(You)", "").strip()
        cleaned = clean_participant_name(name)
        if cleaned and not is_bot:
            real_participants.append(p)
    
    settings = get_settings()
    
    return {
        "platform": platform,
        "url": page.url,
        "total_participants": len(participants),
        "real_participants": len(real_participants),
        "participant_names": [p.get("name") for p in participants],
        "real_participant_names": [p.get("name") for p in real_participants],
        "bot_display_name": settings.bot_display_name,
        "empty_indicators_found": found_indicators,
        "should_leave": len(real_participants) == 0 and len(participants) <= 1,
    }


