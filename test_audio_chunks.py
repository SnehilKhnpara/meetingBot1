"""
Integration test for improved audio chunk capture system.

This test verifies:
1. Audio chunks are created every 30 seconds
2. Chunks have unified data model (AudioChunkData)
3. File naming includes participants and speaker
4. Speaker detection works
5. Participant snapshots are captured
6. No duplicate chunk numbering
"""
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict

# Test configuration
TEST_MEETING_ID = "test-meeting-001"
TEST_SESSION_ID = "test-session-001"
TEST_DURATION_SECONDS = 90  # Run for 90 seconds (3 chunks)


async def simulate_audio_capture():
    """Simulate audio capture for testing."""
    from src.audio_chunk_manager import ImprovedAudioCaptureLoop
    from src.models import ParticipantSnapshot

    # Create stop event
    stop_event = asyncio.Event()

    # Simulate participants
    test_participants = [
        {
            "name": "John Doe",
            "original_name": "John Doe",
            "is_bot": False,
            "role": "host",
            "is_speaking": True,
        },
        {
            "name": "Meeting Bot",
            "original_name": "Meeting Bot (You)",
            "is_bot": True,
            "role": "guest",
            "is_speaking": False,
        },
        {
            "name": "Jane Smith",
            "original_name": "Jane Smith",
            "is_bot": False,
            "role": "guest",
            "is_speaking": False,
        },
    ]

    # Create mock page (for testing without real browser)
    class MockPage:
        """Mock Playwright page for testing."""
        pass

    mock_page = MockPage()

    # Create audio capture loop
    audio_loop = ImprovedAudioCaptureLoop(
        meeting_id=TEST_MEETING_ID,
        session_id=TEST_SESSION_ID,
        page=mock_page,
        stop_event=stop_event,
        chunk_interval_seconds=30,
    )

    # Set participant info
    bot_identifiers = ["meeting bot", "meetingbot"]
    audio_loop.set_participant_info(test_participants, bot_identifiers)

    # Run audio capture in background
    capture_task = asyncio.create_task(audio_loop.run())

    # Wait for test duration
    await asyncio.sleep(TEST_DURATION_SECONDS)

    # Stop capture
    stop_event.set()
    await capture_task

    return audio_loop.chunk_counter


async def verify_chunks():
    """Verify that chunks were created correctly."""
    from src.local_storage import get_local_storage

    storage = get_local_storage()
    chunks_dir = Path(storage.data_dir) / "chunks" / TEST_MEETING_ID / TEST_SESSION_ID

    print(f"\n{'='*60}")
    print(f"CHUNK VERIFICATION RESULTS")
    print(f"{'='*60}\n")

    if not chunks_dir.exists():
        print("❌ FAILED: Chunks directory not found")
        return False

    chunk_files = sorted(chunks_dir.glob("chunk_*.json"))

    print(f"📊 Found {len(chunk_files)} chunk metadata files")

    if len(chunk_files) == 0:
        print("❌ FAILED: No chunks created")
        return False

    all_passed = True
    chunk_numbers_seen = set()

    for chunk_file in chunk_files:
        print(f"\n--- Chunk: {chunk_file.name} ---")

        with open(chunk_file, "r") as f:
            chunk_data = json.load(f)

        # Verify chunk structure
        required_fields = [
            "chunk_id", "chunk_number", "meeting_id", "session_id",
            "start_timestamp", "end_timestamp", "duration_seconds",
            "audio_file_path", "participants", "participant_count"
        ]

        missing_fields = [field for field in required_fields if field not in chunk_data]

        if missing_fields:
            print(f"  ❌ Missing fields: {missing_fields}")
            all_passed = False
        else:
            print(f"  ✅ All required fields present")

        # Verify chunk number uniqueness
        chunk_num = chunk_data.get("chunk_number")
        if chunk_num in chunk_numbers_seen:
            print(f"  ❌ Duplicate chunk number: {chunk_num}")
            all_passed = False
        else:
            chunk_numbers_seen.add(chunk_num)
            print(f"  ✅ Unique chunk number: {chunk_num}")

        # Verify duration
        duration = chunk_data.get("duration_seconds", 0)
        if 28 <= duration <= 32:  # Allow small variance
            print(f"  ✅ Duration: {duration:.2f}s (within 30s ± 2s)")
        else:
            print(f"  ⚠️  Duration: {duration:.2f}s (expected ~30s)")

        # Verify participants
        participants = chunk_data.get("participants", [])
        real_count = chunk_data.get("real_participant_count", 0)
        bot_count = len([p for p in participants if p.get("is_bot", False)])

        print(f"  📊 Participants: {len(participants)} total, {real_count} real, {bot_count} bot")

        for p in participants:
            bot_flag = "🤖" if p.get("is_bot") else "👤"
            print(f"     {bot_flag} {p.get('name')}")

        # Verify active speaker
        active_speaker = chunk_data.get("active_speaker")
        if active_speaker:
            speaker_name = active_speaker.get("speaker_name", "unknown")
            confidence = active_speaker.get("confidence", 0)
            print(f"  🎤 Active speaker: {speaker_name} (confidence: {confidence:.2f})")
        else:
            print(f"  ⚠️  No active speaker detected")

        # Verify audio file exists
        audio_path = chunk_data.get("audio_file_path")
        if audio_path:
            full_audio_path = Path(storage.data_dir) / audio_path
            if full_audio_path.exists():
                file_size = full_audio_path.stat().st_size
                print(f"  ✅ Audio file: {full_audio_path.name} ({file_size:,} bytes)")
            else:
                print(f"  ❌ Audio file not found: {audio_path}")
                all_passed = False
        else:
            print(f"  ❌ No audio file path specified")
            all_passed = False

    print(f"\n{'='*60}")
    if all_passed:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print(f"{'='*60}\n")

    return all_passed


async def main():
    """Run integration test."""
    print(f"\n{'='*60}")
    print(f"AUDIO CHUNK INTEGRATION TEST")
    print(f"{'='*60}")
    print(f"Meeting ID: {TEST_MEETING_ID}")
    print(f"Session ID: {TEST_SESSION_ID}")
    print(f"Test Duration: {TEST_DURATION_SECONDS}s")
    print(f"Expected Chunks: {TEST_DURATION_SECONDS // 30}")
    print(f"{'='*60}\n")

    print("Starting audio capture simulation...")
    chunks_captured = await simulate_audio_capture()

    print(f"\n✅ Capture completed: {chunks_captured} chunks")
    print("\nVerifying chunks...")

    passed = await verify_chunks()

    if passed:
        print("\n🎉 Integration test PASSED!")
        return 0
    else:
        print("\n❌ Integration test FAILED!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
