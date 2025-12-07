# 📁 Local Storage Guide

## What's Stored Locally

All meeting bot data is now saved **locally on your machine** in JSON files and audio files. No Azure needed!

---

## 📂 Directory Structure

All data is stored in the `data/` folder:

```
data/
├── audio/              # Audio files (WAV)
│   └── meeting_id/
│       └── session_id/
│           └── chunk_*.wav
├── events/             # Event logs (JSONL)
│   └── YYYYMMDD.jsonl  # One file per day
└── sessions/           # Session data (JSON)
    └── session_id.json # One file per session
```

---

## 📄 Files Explained

### 1. Events (`data/events/YYYYMMDD.jsonl`)

**Format:** JSON Lines (one JSON object per line)

**Example:**
```json
{"timestamp": "2025-12-03T11:38:31.000Z", "event_type": "bot_joined", "payload": {"meeting_id": "demo-1", ...}}
{"timestamp": "2025-12-03T11:38:35.000Z", "event_type": "session_joined", "payload": {...}}
{"timestamp": "2025-12-03T11:39:00.000Z", "event_type": "audio_chunk_created", "payload": {...}}
```

**Events tracked:**
- `bot_joined` - Bot started joining
- `session_joined` - Successfully joined meeting
- `audio_chunk_created` - New audio chunk saved
- `active_speaker` - Speaker identified
- `participant_update` - Participants changed
- `meeting_summary` - Meeting ended with full summary

---

### 2. Audio Files (`data/audio/meeting_id/session_id/chunk_*.wav`)

**Format:** WAV audio files (30 seconds each)

**Structure:**
```
data/audio/
  └── demo-1/                    # Meeting ID
      └── abc-123-uuid/          # Session ID
          ├── abc-123-uuid-0.wav # Chunk 0
          ├── abc-123-uuid-1.wav # Chunk 1
          └── abc-123-uuid-2.wav # Chunk 2
```

**Note:** Currently generates silent placeholder WAVs. You can replace with real audio capture.

---

### 3. Session Data (`data/sessions/session_id.json`)

**Format:** JSON file with complete session summary

**Example:**
```json
{
  "meeting_id": "demo-1",
  "platform": "gmeet",
  "session_id": "abc-123-uuid",
  "duration_seconds": 120,
  "participants": [
    {
      "name": "John Doe",
      "join_time": "2025-12-03T11:38:31.000Z",
      "leave_time": "2025-12-03T11:40:15.000Z"
    }
  ],
  "audio_chunks": 4,
  "created_at": "2025-12-03T11:38:30.000Z",
  "started_at": "2025-12-03T11:38:31.000Z",
  "ended_at": "2025-12-03T11:40:30.000Z",
  "status": "ended"
}
```

---

## 🎯 Benefits of Local Storage

✅ **No Azure required** - Everything saved on your machine  
✅ **Easy to access** - Just open JSON files in any editor  
✅ **Privacy** - Data stays on your computer  
✅ **Simple debugging** - Check files directly  
✅ **Portable** - Copy `data/` folder to backup  

---

## 🔍 How to View Data

### View Events

**Using text editor:**
```bash
# Windows
notepad data\events\20251203.jsonl

# Or view in terminal
type data\events\20251203.jsonl
```

**Using Python:**
```python
import json

with open('data/events/20251203.jsonl', 'r') as f:
    for line in f:
        event = json.loads(line)
        print(event)
```

### View Session Data

**Using text editor:**
```bash
# Windows
notepad data\sessions\abc-123-uuid.json
```

**Or open in any JSON viewer/editor**

### Listen to Audio Files

Just double-click any `.wav` file in `data/audio/` to play it!

---

## ⚙️ Configuration

### Change Data Directory

Set environment variable before starting:

```cmd
set DATA_DIR=my_custom_folder
start.bat
```

Or in Python:
```python
import os
os.environ["DATA_DIR"] = "my_custom_folder"
```

---

## 🔄 Still Using Azure? (Optional)

If you set Azure environment variables, the bot will:
- ✅ Save locally (as above)
- ✅ Also upload to Azure (backup/cloud sync)

This way you get **both** local files AND cloud backup!

---

## 📊 Example: Reading All Events from Today

```python
import json
from datetime import datetime
from pathlib import Path

# Get today's events file
today = datetime.now().strftime('%Y%m%d')
events_file = Path(f"data/events/{today}.jsonl")

if events_file.exists():
    with open(events_file, 'r') as f:
        for line in f:
            event = json.loads(line)
            print(f"{event['timestamp']} - {event['event_type']}")
            print(f"  {event['payload']}\n")
```

---

## 🎉 That's It!

All your meeting bot data is now stored locally in easy-to-read JSON and audio files. No cloud required! 🚀






