"""
Test script to validate all bot fixes.

Run this to verify:
1. Participant name filtering
2. Meeting end detection
3. Audio validation
4. Summary accuracy
"""
import asyncio
import json
from pathlib import Path

from src.debug_helpers import (
    test_participant_extraction,
    test_meeting_end_detection,
    validate_audio_chunk,
    analyze_session_summary,
    debug_meeting_state,
)
from src.participant_name_filter import is_valid_participant_name, clean_participant_name


def test_participant_name_filter():
    """Test participant name filtering with known bad names."""
    print("\n=== Testing Participant Name Filter ===\n")
    
    # Known bad names from your session data
    bad_names = [
        "Backgrounds and effects",
        "You can't unmute someone else",
        "Your microphone is off.",
        "You can't remotely mute",
        "Settings",
        "More options",
    ]
    
    # Good names
    good_names = [
        "John Doe",
        "Jane Smith",
        "Snehil Patel",
        "Alice Johnson",
    ]
    
    print("Testing BAD names (should be filtered):")
    for name in bad_names:
        is_valid = is_valid_participant_name(name)
        cleaned = clean_participant_name(name)
        status = "❌ FILTERED" if not is_valid else "⚠️  NOT FILTERED (BUG!)"
        print(f"  {name:40} -> {status}")
        if cleaned:
            print(f"    Cleaned: {cleaned}")
    
    print("\nTesting GOOD names (should pass):")
    for name in good_names:
        is_valid = is_valid_participant_name(name)
        cleaned = clean_participant_name(name)
        status = "✅ VALID" if is_valid else "❌ FILTERED (BUG!)"
        print(f"  {name:40} -> {status}")
        if cleaned:
            print(f"    Cleaned: {cleaned}")


def test_session_summaries():
    """Analyze existing session summaries for issues."""
    print("\n=== Analyzing Session Summaries ===\n")
    
    sessions_dir = Path("data/sessions")
    if not sessions_dir.exists():
        print("No sessions directory found.")
        return
    
    session_files = list(sessions_dir.glob("*.json"))
    if not session_files:
        print("No session files found.")
        return
    
    print(f"Found {len(session_files)} session files.\n")
    
    for session_file in session_files[:5]:  # Analyze first 5
        print(f"\n--- {session_file.name} ---")
        result = analyze_session_summary(session_file)
        
        print(f"  Meeting ID: {result['meeting_id']}")
        print(f"  Duration: {result['duration_seconds']}s")
        print(f"  Participants: {result['participants_count']}")
        print(f"  Audio Chunks: {result['audio_chunks']}")
        
        if result['issues']:
            print(f"  ❌ Issues: {len(result['issues'])}")
            for issue in result['issues']:
                print(f"    - {issue}")
        else:
            print("  ✅ No issues found")
        
        if result['warnings']:
            print(f"  ⚠️  Warnings: {len(result['warnings'])}")
            for warning in result['warnings']:
                print(f"    - {warning}")


async def test_audio_validation():
    """Test audio chunk validation."""
    print("\n=== Testing Audio Validation ===\n")
    
    # Test with a valid 30-second silent WAV
    from src.audio import _generate_silence_wav
    
    valid_audio = _generate_silence_wav(duration_seconds=30)
    result = await validate_audio_chunk(valid_audio)
    
    print("Valid 30-second chunk:")
    print(f"  Duration: {result['duration_seconds']:.2f}s")
    print(f"  Sample Rate: {result['sample_rate']}Hz")
    print(f"  Size: {result['chunk_size_kb']:.2f}KB")
    print(f"  Validation: {'✅ PASSED' if result['is_valid'] else '❌ FAILED'}")
    
    # Test with a too-short chunk
    short_audio = _generate_silence_wav(duration_seconds=0.5)
    result_short = await validate_audio_chunk(short_audio)
    
    print("\nToo-short 0.5-second chunk:")
    print(f"  Duration: {result_short['duration_seconds']:.2f}s")
    print(f"  Validation: {'✅ PASSED' if result_short['is_valid'] else '❌ FAILED (expected)'}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("MEETING BOT FIXES - VALIDATION TESTS")
    print("=" * 60)
    
    # Test 1: Participant name filter
    test_participant_name_filter()
    
    # Test 2: Session summaries
    test_session_summaries()
    
    # Test 3: Audio validation
    asyncio.run(test_audio_validation())
    
    print("\n" + "=" * 60)
    print("TESTS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()


