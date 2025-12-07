#!/usr/bin/env python3
"""
Helper script to view all bot data easily.

Usage:
    python view_data.py                    # View all data
    python view_data.py --sessions         # List all sessions
    python view_data.py --events           # Show recent events
    python view_data.py --audio            # Show audio files
    python view_data.py --session [id]     # View specific session
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

DATA_DIR = Path("data")


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def list_sessions() -> List[Dict[str, Any]]:
    """List all session files."""
    sessions_dir = DATA_DIR / "sessions"
    if not sessions_dir.exists():
        return []
    
    sessions = []
    for session_file in sessions_dir.glob("*.json"):
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)
                sessions.append(session_data)
        except Exception as e:
            print(f"Error reading {session_file}: {e}")
    
    return sessions


def show_sessions():
    """Show all sessions summary."""
    print_section("All Sessions")
    
    sessions = list_sessions()
    if not sessions:
        print("No sessions found.")
        return
    
    # Sort by start time (newest first)
    sessions.sort(key=lambda x: x.get("started_at", ""), reverse=True)
    
    print(f"\nFound {len(sessions)} session(s):\n")
    
    for i, session in enumerate(sessions, 1):
        session_id = session.get("session_id", "unknown")
        meeting_id = session.get("meeting_id", "unknown")
        platform = session.get("platform", "unknown")
        status = session.get("status", "unknown")
        
        started = session.get("started_at", "N/A")
        ended = session.get("ended_at", "N/A")
        duration = session.get("duration_seconds", 0)
        
        participants = session.get("participants_history", {})
        participant_count = len([p for p in participants.values() if p.get("leave_time") is None or not p.get("leave_time")])
        total_participants = len(participants)
        
        audio_chunks = session.get("audio_chunks", 0)
        
        print(f"{i}. Session: {session_id[:8]}...")
        print(f"   Meeting: {meeting_id} ({platform})")
        print(f"   Status: {status}")
        print(f"   Started: {started}")
        if ended and ended != "N/A":
            print(f"   Ended: {ended}")
            print(f"   Duration: {duration} seconds ({duration // 60} min)")
        print(f"   Participants: {total_participants} total")
        print(f"   Audio chunks: {audio_chunks}")
        print()


def show_session_detail(session_id: str):
    """Show detailed information about a specific session."""
    session_file = DATA_DIR / "sessions" / f"{session_id}.json"
    
    if not session_file.exists():
        print(f"Session {session_id} not found.")
        print("\nAvailable sessions:")
        for session in list_sessions():
            print(f"  - {session.get('session_id')}")
        return
    
    with open(session_file, "r", encoding="utf-8") as f:
        session_data = json.load(f)
    
    print_section(f"Session Details: {session_id}")
    
    print(f"\nMeeting ID: {session_data.get('meeting_id')}")
    print(f"Platform: {session_data.get('platform')}")
    print(f"Status: {session_data.get('status')}")
    print(f"\nTimeline:")
    print(f"  Created: {session_data.get('created_at')}")
    print(f"  Started: {session_data.get('started_at')}")
    print(f"  Ended: {session_data.get('ended_at')}")
    print(f"  Duration: {session_data.get('duration_seconds', 0)} seconds")
    
    print(f"\nAudio:")
    print(f"  Chunks recorded: {session_data.get('audio_chunks', 0)}")
    
    participants = session_data.get("participants_history", {})
    if participants:
        print(f"\nParticipants ({len(participants)}):")
        for name, info in participants.items():
            join_time = info.get("join_time", "N/A")
            leave_time = info.get("leave_time", "N/A")
            status = "🟢 In meeting" if not leave_time else "🔴 Left"
            print(f"  {status} - {name}")
            print(f"    Joined: {join_time}")
            if leave_time:
                print(f"    Left: {leave_time}")
    else:
        print("\nNo participants recorded.")
    
    # Check for audio files
    meeting_id = session_data.get("meeting_id", "")
    audio_dir = DATA_DIR / "audio" / meeting_id / session_id
    if audio_dir.exists():
        audio_files = list(audio_dir.glob("*.wav"))
        print(f"\nAudio files: {len(audio_files)} found")
        print(f"  Location: {audio_dir}")
    else:
        print(f"\nAudio files: Not found in {audio_dir}")


def show_recent_events(limit: int = 20):
    """Show recent events."""
    print_section(f"Recent Events (Last {limit})")
    
    events_dir = DATA_DIR / "events"
    if not events_dir.exists():
        print("No events found.")
        return
    
    # Get today's events file
    today = datetime.now().strftime("%Y%m%d")
    event_file = events_dir / f"{today}.jsonl"
    
    if not event_file.exists():
        # Try to find any event file
        event_files = sorted(events_dir.glob("*.jsonl"), reverse=True)
        if not event_files:
            print("No event files found.")
            return
        event_file = event_files[0]
        print(f"Showing events from: {event_file.name}\n")
    
    events = []
    try:
        with open(event_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except:
                        continue
    except Exception as e:
        print(f"Error reading events: {e}")
        return
    
    if not events:
        print("No events found.")
        return
    
    # Show last N events
    for event in events[-limit:]:
        timestamp = event.get("timestamp", "N/A")
        event_type = event.get("event_type", "unknown")
        payload = event.get("payload", {})
        
        print(f"\n[{timestamp}] {event_type}")
        
        if event_type == "session_joined":
            print(f"  Meeting: {payload.get('meeting_id')} | Session: {payload.get('session_id', '')[:8]}...")
        elif event_type == "audio_chunk_created":
            print(f"  Meeting: {payload.get('meeting_id')} | Session: {payload.get('session_id', '')[:8]}...")
            print(f"  Chunk: {payload.get('chunk_id')}")
        elif event_type == "participant_update":
            participants = payload.get("participants", [])
            print(f"  Participants: {len(participants)}")
            for p in participants[:3]:  # Show first 3
                print(f"    - {p.get('name')}")
            if len(participants) > 3:
                print(f"    ... and {len(participants) - 3} more")


def show_audio_files():
    """Show all audio files."""
    print_section("Audio Files")
    
    audio_dir = DATA_DIR / "audio"
    if not audio_dir.exists():
        print("No audio directory found.")
        return
    
    total_files = 0
    total_size = 0
    
    print("\nAudio files by meeting:\n")
    
    for meeting_dir in sorted(audio_dir.iterdir()):
        if not meeting_dir.is_dir():
            continue
        
        meeting_id = meeting_dir.name
        session_dirs = list(meeting_dir.iterdir())
        
        print(f"Meeting: {meeting_id}")
        
        for session_dir in session_dirs:
            if not session_dir.is_dir():
                continue
            
            session_id = session_dir.name
            audio_files = list(session_dir.glob("*.wav"))
            file_count = len(audio_files)
            total_files += file_count
            
            if audio_files:
                total_size += sum(f.stat().st_size for f in audio_files)
            
            if file_count > 0:
                print(f"  Session: {session_id[:8]}... | Files: {file_count}")
                print(f"    Path: {session_dir}")
    
    print(f"\nTotal: {total_files} audio files")
    if total_size > 0:
        size_mb = total_size / (1024 * 1024)
        print(f"Total size: {size_mb:.2f} MB")


def main():
    """Main function."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "--sessions":
            show_sessions()
        elif command == "--events":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            show_recent_events(limit)
        elif command == "--audio":
            show_audio_files()
        elif command == "--session":
            if len(sys.argv) > 2:
                show_session_detail(sys.argv[2])
            else:
                print("Usage: python view_data.py --session [session_id]")
        else:
            print("Unknown command. Use --sessions, --events, --audio, or --session [id]")
    else:
        # Show everything
        show_sessions()
        show_recent_events(10)
        show_audio_files()
        
        print("\n" + "=" * 60)
        print("  Quick Commands")
        print("=" * 60)
        print("\npython view_data.py --sessions         # List all sessions")
        print("python view_data.py --events [N]        # Show last N events")
        print("python view_data.py --audio             # Show audio files")
        print("python view_data.py --session [id]      # View specific session")


if __name__ == "__main__":
    main()



