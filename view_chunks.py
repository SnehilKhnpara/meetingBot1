"""
Utility to view audio chunk data in a readable format.

Usage:
    python view_chunks.py                    # Show all chunks
    python view_chunks.py <meeting_id>       # Show chunks for specific meeting
    python view_chunks.py <meeting_id> <session_id>  # Show chunks for specific session
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


def format_timestamp(iso_str: str) -> str:
    """Format ISO timestamp to readable format."""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return iso_str


def print_chunk_summary(chunk_data: Dict[str, Any], chunk_file: Path) -> None:
    """Print a formatted summary of a chunk."""
    chunk_num = chunk_data.get("chunk_number", "?")
    chunk_id = chunk_data.get("chunk_id", "unknown")

    print(f"\n{'='*80}")
    print(f"  CHUNK #{chunk_num:03d} - {chunk_id}")
    print(f"{'='*80}")

    # Time info
    start_time = format_timestamp(chunk_data.get("start_timestamp", ""))
    end_time = format_timestamp(chunk_data.get("end_timestamp", ""))
    duration = chunk_data.get("duration_seconds", 0)

    print(f"\n⏰ TIME:")
    print(f"   Start:    {start_time}")
    print(f"   End:      {end_time}")
    print(f"   Duration: {duration:.2f}s")

    # Participants
    participants = chunk_data.get("participants", [])
    real_count = chunk_data.get("real_participant_count", 0)
    total_count = chunk_data.get("participant_count", 0)

    print(f"\n👥 PARTICIPANTS ({total_count} total, {real_count} real):")
    for p in participants:
        name = p.get("name", "Unknown")
        role = p.get("role", "guest")
        is_bot = p.get("is_bot", False)
        is_speaking = p.get("is_speaking", False)

        icon = "🤖" if is_bot else "👤"
        speaking_icon = "🎤" if is_speaking else "  "
        role_badge = f"[{role.upper()}]" if role != "guest" else ""

        print(f"   {icon} {speaking_icon} {name} {role_badge}")

    # Active speaker
    active_speaker = chunk_data.get("active_speaker")
    if active_speaker:
        speaker_name = active_speaker.get("speaker_name", "Unknown")
        speaker_label = active_speaker.get("speaker_label", "")
        confidence = active_speaker.get("confidence", 0)
        is_bot = active_speaker.get("is_bot", False)

        bot_indicator = "🤖 (BOT)" if is_bot else ""
        print(f"\n🎤 ACTIVE SPEAKER:")
        print(f"   Name:       {speaker_name} {bot_indicator}")
        print(f"   Label:      {speaker_label}")
        print(f"   Confidence: {confidence:.2f}")
    else:
        print(f"\n🎤 ACTIVE SPEAKER: None detected")

    # All speakers
    all_speakers = chunk_data.get("all_speakers", [])
    if len(all_speakers) > 1:
        print(f"\n🔊 ALL SPEAKERS ({len(all_speakers)}):")
        for speaker in all_speakers:
            name = speaker.get("speaker_name", speaker.get("speaker_label", "Unknown"))
            conf = speaker.get("confidence", 0)
            print(f"   • {name} (confidence: {conf:.2f})")

    # Audio file
    audio_path = chunk_data.get("audio_file_path", "")
    audio_size = chunk_data.get("audio_file_size_bytes", 0)

    print(f"\n🎵 AUDIO FILE:")
    if audio_path:
        print(f"   Path: {audio_path}")
        print(f"   Size: {audio_size:,} bytes ({audio_size/1024:.2f} KB)")

        # Check if file exists
        data_dir = Path("data")
        full_path = data_dir / audio_path
        if full_path.exists():
            actual_size = full_path.stat().st_size
            print(f"   Status: ✅ Exists ({actual_size:,} bytes)")
        else:
            print(f"   Status: ❌ Not found")
    else:
        print(f"   Status: ❌ No audio file")

    # Metadata file
    print(f"\n📄 METADATA:")
    print(f"   File: {chunk_file.name}")
    print(f"   Size: {chunk_file.stat().st_size:,} bytes")


def list_all_sessions(data_dir: Path) -> List[tuple]:
    """List all available (meeting_id, session_id) pairs."""
    chunks_dir = data_dir / "chunks"
    if not chunks_dir.exists():
        return []

    sessions = []
    for meeting_dir in chunks_dir.iterdir():
        if meeting_dir.is_dir():
            meeting_id = meeting_dir.name
            for session_dir in meeting_dir.iterdir():
                if session_dir.is_dir():
                    session_id = session_dir.name
                    chunk_count = len(list(session_dir.glob("chunk_*.json")))
                    sessions.append((meeting_id, session_id, chunk_count))

    return sessions


def view_chunks(meeting_id: str = None, session_id: str = None) -> None:
    """View chunks with optional filtering."""
    data_dir = Path("data")
    chunks_dir = data_dir / "chunks"

    if not chunks_dir.exists():
        print("❌ No chunks directory found. Have you run any meetings yet?")
        return

    # List all sessions if no filtering
    if not meeting_id:
        print(f"\n{'='*80}")
        print(f"  AVAILABLE SESSIONS")
        print(f"{'='*80}\n")

        sessions = list_all_sessions(data_dir)

        if not sessions:
            print("❌ No sessions found.")
            return

        print(f"Found {len(sessions)} session(s):\n")
        for meeting_id, session_id, chunk_count in sessions:
            print(f"  📊 Meeting: {meeting_id}")
            print(f"     Session: {session_id}")
            print(f"     Chunks: {chunk_count}")
            print()

        print("\nTo view chunks for a specific session, run:")
        print(f"  python view_chunks.py <meeting_id> <session_id>")
        return

    # View specific session
    session_chunks_dir = chunks_dir / meeting_id / session_id

    if not session_chunks_dir.exists():
        print(f"❌ No chunks found for meeting '{meeting_id}', session '{session_id}'")
        return

    chunk_files = sorted(session_chunks_dir.glob("chunk_*.json"))

    if not chunk_files:
        print(f"❌ No chunk files found in {session_chunks_dir}")
        return

    print(f"\n{'='*80}")
    print(f"  CHUNKS FOR SESSION")
    print(f"{'='*80}")
    print(f"  Meeting ID:  {meeting_id}")
    print(f"  Session ID:  {session_id}")
    print(f"  Total Chunks: {len(chunk_files)}")
    print(f"{'='*80}")

    for chunk_file in chunk_files:
        try:
            with open(chunk_file, "r", encoding="utf-8") as f:
                chunk_data = json.load(f)
            print_chunk_summary(chunk_data, chunk_file)
        except Exception as e:
            print(f"\n❌ Error reading {chunk_file.name}: {e}")

    print(f"\n{'='*80}")
    print(f"  END OF CHUNKS")
    print(f"{'='*80}\n")


def main():
    """Main entry point."""
    args = sys.argv[1:]

    if len(args) == 0:
        # No args: list all sessions
        view_chunks()
    elif len(args) == 1:
        # One arg: meeting_id (list sessions for that meeting)
        meeting_id = args[0]
        view_chunks(meeting_id=meeting_id)
    elif len(args) >= 2:
        # Two args: meeting_id and session_id
        meeting_id = args[0]
        session_id = args[1]
        view_chunks(meeting_id=meeting_id, session_id=session_id)
    else:
        print("Usage:")
        print("  python view_chunks.py                        # List all sessions")
        print("  python view_chunks.py <meeting_id>           # List sessions for meeting")
        print("  python view_chunks.py <meeting_id> <session_id>  # View chunks")
        sys.exit(1)


if __name__ == "__main__":
    main()
