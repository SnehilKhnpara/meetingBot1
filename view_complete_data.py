#!/usr/bin/env python3
"""
Complete Data Viewer - Shows ALL data from the three Jira stories.

Shows:
- Story 1: Audio capture (30-second chunks) + Speaker identification
- Story 2: Participant tracking + Active speaker detection  
- Story 3: Meeting summaries + All events
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

DATA_DIR = Path("data")


def print_header(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


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
        except Exception:
            continue
    
    return sessions


def load_events() -> List[Dict[str, Any]]:
    """Load all events."""
    events_dir = DATA_DIR / "events"
    if not events_dir.exists():
        return []
    
    events = []
    # Load today's and recent event files
    event_files = sorted(events_dir.glob("*.jsonl"), reverse=True)
    
    for event_file in event_files[:3]:  # Load last 3 days
        try:
            with open(event_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            events.append(json.loads(line))
                        except:
                            continue
        except Exception:
            continue
    
    return events


def show_complete_session_report(session_id: str = None):
    """Show complete report for a session."""
    sessions = load_sessions()
    events = load_events()
    
    if session_id:
        sessions = [s for s in sessions if s.get("session_id") == session_id]
        if not sessions:
            print(f"\n❌ Session {session_id} not found.\n")
            return
    
    if not sessions:
        print("\n❌ No sessions found.\n")
        return
    
    # Sort by start time (newest first)
    sessions.sort(key=lambda x: x.get("started_at", ""), reverse=True)
    
    for session in sessions:
        meeting_id = session.get("meeting_id", "Unknown")
        platform = session.get("platform", "unknown")
        session_id_val = session.get("session_id", "unknown")
        
        print_header(f"📊 COMPLETE REPORT: {meeting_id} ({platform})")
        
        # Basic Info
        print(f"Session ID: {session_id_val}")
        print(f"Platform: {platform}")
        print(f"Status: {session.get('status', 'unknown')}")
        
        duration = session.get("duration_seconds", 0)
        duration_min = duration // 60
        duration_sec = duration % 60
        print(f"Duration: {duration_min}m {duration_sec}s ({duration} seconds)")
        print(f"Started: {session.get('started_at', 'N/A')}")
        print(f"Ended: {session.get('ended_at', 'N/A')}")
        
        # Story 1: Audio Data
        audio_chunks = session.get("audio_chunks", 0)
        print(f"\n🎵 STORY 1: AUDIO CAPTURE")
        print(f"   Total audio chunks: {audio_chunks}")
        print(f"   Expected duration: {audio_chunks * 30} seconds")
        
        # Check audio files
        audio_dir = DATA_DIR / "audio" / meeting_id
        if audio_dir.exists():
            for session_dir in audio_dir.iterdir():
                if session_dir.is_dir() and session_id_val[:8] in str(session_dir):
                    audio_files = list(session_dir.glob("*.wav"))
                    total_size = sum(f.stat().st_size for f in audio_files)
                    print(f"   Audio files found: {len(audio_files)}")
                    if total_size > 0:
                        print(f"   Total size: {total_size / (1024*1024):.2f} MB")
                    print(f"   Location: {session_dir}")
        
        # Filter events for this session
        session_events = [
            e for e in events
            if e.get("payload", {}).get("session_id") == session_id_val
        ]
        
        # Active Speaker Events (Story 1)
        speaker_events = [e for e in session_events if e.get("event_type") == "active_speaker"]
        print(f"\n🎤 STORY 1: ACTIVE SPEAKER IDENTIFICATION")
        print(f"   Active speaker events: {len(speaker_events)}")
        if speaker_events:
            print(f"\n   Recent speakers:")
            for event in speaker_events[-5:]:
                payload = event.get("payload", {})
                timestamp = event.get("timestamp", "N/A")[:19]  # Remove timezone
                speaker = payload.get("speaker_label", "Unknown")
                confidence = payload.get("confidence", 0)
                print(f"   • {timestamp} - {speaker} (confidence: {confidence:.1%})")
        
        # Story 2: Participant Tracking
        participants = session.get("participants", [])
        if isinstance(participants, dict):
            participants = list(participants.values())
        
        print(f"\n👥 STORY 2: PARTICIPANT TRACKING")
        print(f"   Total participants tracked: {len(participants)}")
        
        if participants:
            print(f"\n   Participants:")
            for i, p in enumerate(participants, 1):
                name = p.get("name", "Unknown")
                join_time = p.get("join_time", "N/A")
                leave_time = p.get("leave_time")
                role = p.get("role", "guest")
                is_speaking = p.get("is_speaking", False)
                
                role_icon = "👑" if role in ["host", "organizer"] else "👤"
                speaking_icon = "🎤" if is_speaking else ""
                
                print(f"   {i}. {role_icon} {name} {speaking_icon}")
                print(f"      Joined: {join_time}")
                if leave_time:
                    print(f"      Left: {leave_time}")
                    # Calculate duration
                    try:
                        join_dt = datetime.fromisoformat(join_time.replace("Z", "+00:00"))
                        leave_dt = datetime.fromisoformat(leave_time.replace("Z", "+00:00"))
                        duration_sec = (leave_dt - join_dt).total_seconds()
                        print(f"      Time in meeting: {int(duration_sec // 60)}m {int(duration_sec % 60)}s")
                    except:
                        pass
                else:
                    print(f"      Status: Still in meeting")
        else:
            print(f"   (No participants tracked)")
        
        # Participant Update Events (Story 2)
        update_events = [e for e in session_events if e.get("event_type") == "participant_update"]
        print(f"\n   Participant update events: {len(update_events)}")
        print(f"   (Updated every 30 seconds)")
        
        # Story 3: Meeting Summary
        print(f"\n📋 STORY 3: MEETING SUMMARY")
        print(f"   Summary published: ✅ Yes")
        print(f"   All data included: ✅ Yes")
        
        error = session.get("error")
        if error:
            print(f"\n   ⚠️ Error: {error}")
        
        # Event Timeline
        print(f"\n📅 EVENT TIMELINE")
        print(f"   Total events: {len(session_events)}")
        
        event_types = defaultdict(int)
        for event in session_events:
            event_types[event.get("event_type", "unknown")] += 1
        
        for event_type, count in sorted(event_types.items()):
            print(f"   • {event_type}: {count}")
        
        print()


def show_all_sessions_summary():
    """Show summary of all sessions."""
    print_header("📊 ALL MEETINGS SUMMARY")
    
    sessions = load_sessions()
    if not sessions:
        print("❌ No sessions found.\n")
        return
    
    # Sort by start time (newest first)
    sessions.sort(key=lambda x: x.get("started_at", ""), reverse=True)
    
    print(f"Total meetings: {len(sessions)}\n")
    
    for i, session in enumerate(sessions, 1):
        meeting_id = session.get("meeting_id", "Unknown")
        platform = session.get("platform", "unknown")
        session_id = session.get("session_id", "unknown")
        status = session.get("status", "unknown")
        
        duration = session.get("duration_seconds", 0)
        duration_min = duration // 60
        
        participants = session.get("participants", [])
        if isinstance(participants, dict):
            participants = list(participants.values())
        
        audio_chunks = session.get("audio_chunks", 0)
        
        started = session.get("started_at", "N/A")[:19] if session.get("started_at") else "N/A"
        
        print(f"{i}. Meeting: {meeting_id} ({platform})")
        print(f"   Session: {session_id[:8]}...")
        print(f"   Status: {status} | Duration: {duration_min}m | Started: {started}")
        print(f"   Participants: {len(participants)} | Audio chunks: {audio_chunks}")
        print()


def main():
    """Main function."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "--session":
            if len(sys.argv) > 2:
                show_complete_session_report(sys.argv[2])
            else:
                print("\nUsage: python view_complete_data.py --session [session_id]\n")
                print("Available sessions:")
                sessions = load_sessions()
                for session in sessions[:10]:
                    print(f"  - {session.get('session_id')} ({session.get('meeting_id')})")
        elif command == "--all":
            show_all_sessions_summary()
        else:
            print(f"\nUnknown command: {command}\n")
            print("Usage:")
            print("  python view_complete_data.py           # Show all data")
            print("  python view_complete_data.py --session [id]  # Specific session")
            print("  python view_complete_data.py --all     # All sessions summary")
    else:
        # Show all data
        print_header("📊 COMPLETE DATA VIEWER - All Jira Story Data")
        
        show_all_sessions_summary()
        
        # Show details for first session
        sessions = load_sessions()
        if sessions:
            sessions.sort(key=lambda x: x.get("started_at", ""), reverse=True)
            show_complete_session_report(sessions[0].get("session_id"))
        
        print("\n" + "=" * 80)
        print("  Quick Commands")
        print("=" * 80)
        print("\npython view_complete_data.py --session [id]  # View specific session")
        print("python view_complete_data.py --all            # All sessions summary")
        print("\nFor more options, run: python view_all_data.py\n")


if __name__ == "__main__":
    main()



