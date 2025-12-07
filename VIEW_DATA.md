# 📊 How to Check All Bot Data

## 🎯 Quick Overview

All data is stored in the **`data/`** folder. Here's what's there:

```
data/
├── audio/           # All audio recordings (WAV files)
├── events/          # All events (JSON Lines files)
├── sessions/        # Session summaries (JSON files)
└── error_*.png      # Screenshots when errors occur
```

---

## 📁 1. View Audio Files

### Location
```
data/audio/meeting_id/session_id/*.wav
```

### Examples
```
data/audio/
  └── AA/
      └── 76fa8b3e-5ef7-44bf-81ed-e7e5fb19b49f/
          ├── chunk-0.wav
          ├── chunk-1.wav
          └── chunk-2.wav
```

### How to View
1. **Navigate to folder:** `data\audio\[meeting_id]\[session_id]\`
2. **Double-click any `.wav` file** to play in your default media player
3. **Or use Windows Media Player / VLC**

### Find All Audio Files
```cmd
REM Windows - open audio folder
explorer data\audio

REM List all audio files
dir /s /b data\audio\*.wav
```

---

## 📄 2. View Session Data

### Location
```
data/sessions/session_id.json
```

### What's Inside
Each session file contains:
- Meeting ID and URL
- Session start/end times
- Duration
- Participant list with join/leave times
- Number of audio chunks recorded
- Status (ended, failed, etc.)

### How to View

**Option 1: Text Editor**
```cmd
REM Open any session file
notepad data\sessions\[session_id].json
```

**Option 2: JSON Viewer (Better)**
- Use VS Code, Notepad++, or any JSON viewer
- Or paste into: https://jsonviewer.stack.hu/

**Option 3: Command Line**
```cmd
REM List all sessions
dir data\sessions\*.json

REM View a specific session (formatted)
type data\sessions\[session_id].json
```

### Example Session File
```json
{
  "meeting_id": "AA",
  "platform": "gmeet",
  "session_id": "abc-123",
  "duration_seconds": 120,
  "participants": [
    {
      "name": "John Doe",
      "join_time": "2025-12-04T20:45:00+00:00",
      "leave_time": "2025-12-04T20:47:00+00:00"
    }
  ],
  "audio_chunks": 4,
  "created_at": "2025-12-04T20:44:00+00:00",
  "started_at": "2025-12-04T20:45:00+00:00",
  "ended_at": "2025-12-04T20:47:00+00:00",
  "status": "ended"
}
```

---

## 📋 3. View Events

### Location
```
data/events/YYYYMMDD.jsonl
```
One file per day, in JSON Lines format (one JSON object per line).

### Event Types
- `bot_joined` - Bot started joining
- `session_joined` - Successfully joined meeting
- `audio_chunk_created` - New audio chunk saved
- `participant_update` - Participants changed
- `meeting_summary` - Meeting ended

### How to View

**Option 1: Text Editor**
```cmd
REM Open today's events
notepad data\events\20251204.jsonl
```

**Option 2: Command Line (Last 10 Events)**
```cmd
powershell "Get-Content data\events\20251204.jsonl -Tail 10"
```

**Option 3: Python Script** (See `view_data.py` below)

### Example Event
```json
{
  "timestamp": "2025-12-04T20:45:00+00:00",
  "event_type": "session_joined",
  "payload": {
    "meeting_id": "AA",
    "session_id": "abc-123",
    "platform": "gmeet"
  }
}
```

---

## 🔍 4. View Error Screenshots

### Location
```
data/error_[session_id]_[timestamp].png
data/error_[session_id]_state.json
```

### How to View
1. **Open folder:** `data\`
2. **Look for files starting with `error_`**
3. **Double-click `.png` files** to view screenshots
4. **Open `.json` files** to see page state when error occurred

---

## 🛠️ Quick Access Commands

### Open Data Folder
```cmd
explorer data
```

### List All Sessions
```cmd
dir /b data\sessions\*.json
```

### List All Audio Files
```cmd
dir /s /b data\audio\*.wav
```

### View Today's Events
```cmd
type data\events\%date:~-4,4%%date:~-7,2%%date:~-10,2%.jsonl
```

---

## 📊 Using the Dashboard

### View Sessions
1. Open dashboard: `http://localhost:8000`
2. Go to **"Active Sessions"** section
3. See all sessions with status, participants, duration

### View Live Logs
1. Open dashboard: `http://localhost:8000`
2. Go to **"Live Logs"** section
3. Filter by level, search by meeting/session ID

---

## 🐍 Python Script to View Data

I've created a helper script - see `view_data.py` below or run:
```cmd
python view_data.py
```

This will show:
- All sessions summary
- Audio files count
- Recent events
- Easy navigation

---

## 📈 Data Statistics

### Count Total Audio Files
```cmd
dir /s /b data\audio\*.wav | find /c ".wav"
```

### Count Total Sessions
```cmd
dir /b data\sessions\*.json | find /c ".json"
```

### Total Size of Data
```cmd
dir /s data
```

---

## 💡 Tips

1. **Sort by Date:** Files are organized by date (events) or session (audio)
2. **Use JSON Viewers:** For better formatting of JSON files
3. **Search Events:** Use text search in JSONL files to find specific events
4. **Backup Data:** Copy entire `data/` folder to backup all your data

---

## 🔗 Quick Links

- **Audio Folder:** `data\audio\`
- **Sessions Folder:** `data\sessions\`
- **Events Folder:** `data\events\`
- **Dashboard:** `http://localhost:8000`

---

**Everything is stored locally in the `data/` folder - easy to access!** 📁



