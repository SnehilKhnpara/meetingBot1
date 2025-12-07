#!/usr/bin/env python3
"""
Comprehensive Data Viewer - Shows ALL data from the three Jira stories.

Shows:
- Participant tracking data (names, join/leave times, roles)
- Active speaker information
- Audio chunk information
- Meeting summaries
- All events from the stories
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

DATA_DIR = Path("data")


def print_section(title: str, char: str = "="):
    """Print a section header."""
    print("\n" + char * 70)
    print(f"  {title}")
    print(char * 70)


def load_sessions() -> List[Dict[str, Any]]:
    """Load all session files."""
    sessions_dir = DATA_DIR / "sessions"
    if not sessions_dir.exists():
        return []
    
    sessions = []
    for session_file in sessions_dir.glob("*.json"):
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                sessions.append(json.load(f))
        except Exception as e:
            print(f"Error loading {session_file}: {e}")
    
    return sessions


def load_events() -> List[Dict[str, Any]]:
    """Load all events from today's file."""
    events_dir = DATA_DIR / "events"
    if not events_dir.exists():
        return []
    
    events = []
    # Load today's events
    today = datetime.now().strftime("%Y%m%d")
    event_file = events_dir / f"{today}.jsonl"
    
    if not event_file.exists():
        # Try to find any event file
        event_files = sorted(events_dir.glob("*.jsonl"), reverse=True)
        if event_files:
            event_file = event_files[0]
    
    if event_file.exists():
        try:
            with open(event_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            events.append(json.loads(line))
                        except:
                            continue
        except Exception as e:
            print(f"Error loading events: {e}")
    
    return events


def show_all_participants():
    """Show all participant data from all sessions."""
    print_section("📋 ALL PARTICIPANTS - Join/Leave Times & Roles")
    
    sessions = load_sessions()
    if not sessions:
        print("No sessions found.")
        return
    
    all_participants = {}
    
    for session in sessions:
        meeting_id = session.get("meeting_id", "unknown")
        session_id = session.get("session_id", "unknown")
        platform = session.get("platform", "unknown")
        started = session.get("started_at", "N/A")
        
        participants = session.get("participants", [])
        if isinstance(participants, dict):
            # Convert dict to list
            participants = list(participants.values())
        
        print(f"\n📅 Meeting: {meeting_id} ({platform})")
        print(f"   Session: {session_id[:8]}...")
        print(f"   Started: {started}")
        print(f"   Participants: {len(participants)}")
        
        if participants:
            for p in participants:
                name = p.get("name", "Unknown")
                join_time = p.get("join_time", "N/A")
                leave_time = p.get("leave_time")
                role = p.get("role", "guest")
                
                # Track unique participants across all meetings
                if name not in all_participants:
                    all_participants[name] = {
                        "name": name,
                        "meetings": [],
                        "total_time": 0,
                    }
                
                duration_text = "Still in meeting" if not leave_time else f"Left: {leave_time}"
                role_icon = "👑" if role == "host" or role == "organizer" else "👤"
                
                print(f"   {role_icon} {name}")
                print(f"      Joined: {join_time}")
                print(f"      {duration_text}")
                print(f"      Role: {role}")
        else:
            print("   (No participants tracked)")
        print()
    
    print(f"\n📊 Total unique participants across all meetings: {len(all_participants)}")


def show_active_speakers():
    """Show all active speaker events."""
    print_section("🎤 ACTIVE SPEAKER DETECTION")
    
    events = load_events()
    speaker_events = [e for e in events if e.get("event_type") == "active_speaker"]
    
    if not speaker_events:
        print("No active speaker events found.")
        return
    
    print(f"\nFound {len(speaker_events)} active speaker events:\n")
    
    # Group by meeting
    by_meeting = defaultdict(list)
    for event in speaker_events:
        payload = event.get("payload", {})
        meeting_id = payload.get("meeting_id", "unknown")
        by_meeting[meeting_id].append(event)
    
    for meeting_id, meeting_events in by_meeting.items():
        print(f"📅 Meeting: {meeting_id}")
        print(f"   Active speaker events: {len(meeting_events)}\n")
        
        for event in meeting_events[-10:]:  # Show last 10
            payload = event.get("payload", {})
            timestamp = event.get("timestamp", "N/A")
            speaker = payload.get("speaker_label", "Unknown")
            confidence = payload.get("confidence", 0)
            chunk_id = payload.get("chunk_id", "N/A")
            
            print(f"   ⏰ {timestamp}")
            print(f"      Speaker: {speaker}")
            print(f"      Confidence: {confidence:.2%}")
            print(f"      Chunk: {chunk_id[:20]}...")
            print()


def show_participant_updates():
    """Show all participant update events."""
    print_section("👥 PARTICIPANT UPDATES (Join/Leave Events)")
    
    events = load_events()
    update_events = [e for e in events if e.get("event_type") == "participant_update"]
    
    if not update_events:
        print("No participant update events found.")
        return
    
    print(f"\nFound {len(update_events)} participant update events:\n")
    
    for event in update_events[-5:]:  # Show last 5
        payload = event.get("payload", {})
        timestamp = event.get("timestamp", "N/A")
        meeting_id = payload.get("meeting_id", "unknown")
        participants = payload.get("participants", [])
        
        print(f"📅 Meeting: {meeting_id} | {timestamp}")
        print(f"   Participants: {len(participants)}")
        
        for p in participants[:5]:  # Show first 5
            name = p.get("name", "Unknown")
            join_time = p.get("join_time", "N/A")
            leave_time = p.get("leave_time")
            status = "🟢 In meeting" if not leave_time else "🔴 Left"
            print(f"   {status} - {name} (Joined: {join_time})")
        
        if len(participants) > 5:
            print(f"   ... and {len(participants) - 5} more")
        print()


def show_meeting_summaries():
    """Show all meeting summaries."""
    print_section("📊 MEETING SUMMARIES")
    
    sessions = load_sessions()
    if not sessions:
        print("No meeting summaries found.")
        return
    
    # Sort by start time
    sessions.sort(key=lambda x: x.get("started_at", ""), reverse=True)
    
    print(f"\nFound {len(sessions)} meeting summaries:\n")
    
    for session in sessions:
        meeting_id = session.get("meeting_id", "unknown")
        platform = session.get("platform", "unknown")
        session_id = session.get("session_id", "unknown")
        status = session.get("status", "unknown")
        
        duration = session.get("duration_seconds", 0)
        duration_min = duration // 60
        duration_sec = duration % 60
        
        participants = session.get("participants", [])
        if isinstance(participants, dict):
            participants = list(participants.values())
        
        audio_chunks = session.get("audio_chunks", 0)
        
        started = session.get("started_at", "N/A")
        ended = session.get("ended_at", "N/A")
        
        print(f"📅 Meeting: {meeting_id} ({platform})")
        print(f"   Session ID: {session_id}")
        print(f"   Status: {status}")
        print(f"   Duration: {duration_min}m {duration_sec}s ({duration} seconds)")
        print(f"   Started: {started}")
        print(f"   Ended: {ended}")
        print(f"   Participants: {len(participants)}")
        print(f"   Audio chunks: {audio_chunks}")
        
        if participants:
            print(f"\n   Participant Details:")
            for p in participants:
                name = p.get("name", "Unknown")
                join_time = p.get("join_time", "N/A")
                leave_time = p.get("leave_time")
                role = p.get("role", "guest")
                
                if leave_time:
                    # Calculate time in meeting
                    try:
                        join_dt = datetime.fromisoformat(join_time.replace("Z", "+00:00"))
                        leave_dt = datetime.fromisoformat(leave_time.replace("Z", "+00:00"))
                        time_in_meeting = (leave_dt - join_dt).total_seconds()
                        time_str = f"{int(time_in_meeting // 60)}m {int(time_in_meeting % 60)}s"
                    except:
                        time_str = "N/A"
                    print(f"      👤 {name} ({role}) - In meeting: {time_str}")
                    print(f"         Joined: {join_time}")
                    print(f"         Left: {leave_time}")
                else:
                    print(f"      👤 {name} ({role}) - Still in meeting")
                    print(f"         Joined: {join_time}")
        
        error = session.get("error")
        if error:
            print(f"\n   ⚠️ Error: {error}")
        
        print()


def show_audio_statistics():
    """Show audio chunk statistics."""
    print_section("🎵 AUDIO CHUNK STATISTICS")
    
    events = load_events()
    audio_events = [e for e in events if e.get("event_type") == "audio_chunk_created"]
    
    if not audio_events:
        print("No audio chunk events found.")
        return
    
    print(f"\nFound {len(audio_events)} audio chunks:\n")
    
    # Group by meeting
    by_meeting = defaultdict(list)
    for event in audio_events:
        payload = event.get("payload", {})
        meeting_id = payload.get("meeting_id", "unknown")
        by_meeting[meeting_id].append(event)
    
    for meeting_id, meeting_audio in by_meeting.items():
        print(f"📅 Meeting: {meeting_id}")
        print(f"   Total chunks: {len(meeting_audio)}")
        
        # Check file sizes
        total_size = 0
        audio_dir = DATA_DIR / "audio" / meeting_id
        if audio_dir.exists():
            for session_dir in audio_dir.iterdir():
                if session_dir.is_dir():
                    audio_files = list(session_dir.glob("*.wav"))
                    for audio_file in audio_files:
                        total_size += audio_file.stat().st_size
                    
                    print(f"   Session: {session_dir.name[:8]}...")
                    print(f"      Files: {len(audio_files)}")
        
        if total_size > 0:
            size_mb = total_size / (1024 * 1024)
            print(f"   Total size: {size_mb:.2f} MB")
        
        print(f"   Expected duration: {len(meeting_audio) * 30} seconds")
        print()


def show_complete_session_report(session_id: str = None):
    """Show complete report for a specific session or all sessions."""
    sessions = load_sessions()
    events = load_events()
    
    if session_id:
        sessions = [s for s in sessions if s.get("session_id") == session_id]
        if not sessions:
            print(f"Session {session_id} not found.")
            return
    
    if not sessions:
        print("No sessions found.")
        return
    
    for session in sessions:
        print_section(f"📊 COMPLETE REPORT: {session.get('meeting_id', 'Unknown')}")
        
        # Session info
        print(f"\nMeeting ID: {session.get('meeting_id')}")
        print(f"Platform: {session.get('platform')}")
        print(f"Session ID: {session.get('session_id')}")
        print(f"Status: {session.get('status')}")
        print(f"Duration: {session.get('duration_seconds', 0)} seconds")
        print(f"Started: {session.get('started_at')}")
        print(f"Ended: {session.get('ended_at')}")
        
        # Participants
        participants = session.get("participants", [])
        if isinstance(participants, dict):
            participants = list(participants.values())
        
        print(f"\n👥 PARTICIPANTS ({len(participants)}):")
        for p in participants:
            name = p.get("name", "Unknown")
            join_time = p.get("join_time", "N/A")
            leave_time = p.get("leave_time")
            role = p.get("role", "guest")
            
            print(f"  - {name} ({role})")
            print(f"    Joined: {join_time}")
            if leave_time:
                print(f"    Left: {leave_time}")
            else:
                print(f"    Status: Still in meeting")
        
        # Audio chunks
        audio_chunks = session.get("audio_chunks", 0)
        print(f"\n🎵 AUDIO:")
        print(f"  Total chunks: {audio_chunks}")
        print(f"  Expected duration: {audio_chunks * 30} seconds")
        
        # Filter events for this session
        session_id_val = session.get("session_id")
        session_events = [
            e for e in events
            if e.get("payload", {}).get("session_id") == session_id_val
        ]
        
        # Active speakers
        speaker_events = [e for e in session_events if e.get("event_type") == "active_speaker"]
        print(f"\n🎤 ACTIVE SPEAKERS ({len(speaker_events)} events):")
        for event in speaker_events[-5:]:  # Last 5
            payload = event.get("payload", {})
            print(f"  - {payload.get('speaker_label')} (confidence: {payload.get('confidence', 0):.2%})")
            print(f"    Time: {event.get('timestamp')}")
        
        print()


def main():
    """Main function."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "--summary":
            show_meeting_summaries()
        elif command == "--participants":
            show_all_participants()
        elif command == "--speakers":
            show_active_speakers()
        elif command == "--audio":
            show_audio_statistics()
        elif command == "--updates":
            show_participant_updates()
        elif command == "--session":
            if len(sys.argv) > 2:
                show_complete_session_report(sys.argv[2])
            else:
                print("Usage: python view_all_data.py --session [session_id]")
        elif command == "--full":
            show_complete_session_report()
        else:
            print("Unknown command.")
            print_help()
    else:
        # Show everything
        print_section("📊 COMPLETE DATA VIEWER - All Jira Story Data", "=")
        
        show_meeting_summaries()
        show_all_participants()
        show_active_speakers()
        show_participant_updates()
        show_audio_statistics()
        
        print_section("Quick Commands")
        print("\npython view_all_data.py --summary         # Meeting summaries")
        print("python view_all_data.py --participants     # All participants")
        print("python view_all_data.py --speakers         # Active speakers")
        print("python view_all_data.py --audio            # Audio statistics")
        print("python view_all_data.py --updates          # Participant updates")
        print("python view_all_data.py --session [id]     # Complete session report")


def print_help():
    """Print help message."""
    print("\nAvailable commands:")
    print("  --summary          Show meeting summaries")
    print("  --participants     Show all participants")
    print("  --speakers         Show active speakers")
    print("  --audio            Show audio statistics")
    print("  --updates          Show participant updates")
    print("  --session [id]     Show complete session report")
    print("  --full             Show all data")


if __name__ == "__main__":
    main()



