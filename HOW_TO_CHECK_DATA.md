# 📊 How to Check All Bot Data - Quick Guide

## ⚡ Quickest Way

### Option 1: Open Data Folder
```
Double-click: open_data.bat
```
This opens all data folders for easy browsing!

### Option 2: Python Viewer
```cmd
python view_data.py
```
Shows formatted summary of all sessions, events, and audio files.

---

## 📁 Where is Everything?

All data is in the **`data/`** folder:

```
data/
├── audio/           ← Audio recordings (WAV files)
├── events/          ← All events (JSON files)
├── sessions/        ← Session summaries (JSON files)
└── error_*.png      ← Screenshot when errors occur
```

---

## 🎵 View Audio Files

### Method 1: File Explorer
```cmd
explorer data\audio
```
Then navigate to: `meeting_id\session_id\` and double-click any `.wav` file to play!

### Method 2: Quick Open
```cmd
REM List all audio files
dir /s /b data\audio\*.wav
```

### Example Path
```
data\audio\AA\76fa8b3e-5ef7-44bf-81ed-e7e5fb19b49f\chunk-0.wav
```

---

## 📄 View Session Data

### Method 1: File Explorer
```cmd
explorer data\sessions
```
Double-click any `.json` file to open in your text editor!

### Method 2: Python Viewer
```cmd
python view_data.py --sessions
```

### View Specific Session
```cmd
python view_data.py --session [session_id]
```

### Session File Contains:
- Meeting ID and URL
- Start/end times
- Duration
- Participant list (who joined, when they left)
- Number of audio chunks
- Status (ended, failed, etc.)

---

## 📋 View Events

### Method 1: File Explorer
```cmd
explorer data\events
```
Open today's file: `20251204.jsonl` (format: YYYYMMDD.jsonl)

### Method 2: Python Viewer
```cmd
python view_data.py --events 50
```
Shows last 50 events

### Method 3: Command Line
```cmd
REM View last 10 events
powershell "Get-Content data\events\20251204.jsonl -Tail 10"
```

### Event Types:
- `bot_joined` - Bot started joining
- `session_joined` - Successfully joined
- `audio_chunk_created` - New audio saved
- `participant_update` - People joined/left
- `meeting_summary` - Meeting ended

---

## 🌐 Using Dashboard

Open in browser: `http://localhost:8000`

### View Sessions
- See all active/completed sessions
- Click to see details
- View participant counts
- See duration and status

### View Live Logs
- Real-time log viewing
- Filter by level (INFO, ERROR, etc.)
- Search by meeting ID or session ID

---

## 🛠️ Helper Scripts

### `open_data.bat`
Opens all data folders with a menu:
```
Double-click: open_data.bat
```

### `view_data.py`
Python script to view formatted data:
```cmd
python view_data.py                # View everything
python view_data.py --sessions     # List all sessions
python view_data.py --events 20    # Last 20 events
python view_data.py --audio        # All audio files
python view_data.py --session [id] # Specific session
```

---

## 💡 Quick Commands

```cmd
REM Open main data folder
explorer data

REM List all sessions
dir /b data\sessions\*.json

REM List all audio files
dir /s /b data\audio\*.wav

REM Count total audio files
dir /s /b data\audio\*.wav | find /c ".wav"

REM View today's events
type data\events\20251204.jsonl
```

---

## 📊 Example: Finding Specific Meeting Data

Let's say you joined a meeting called "AA":

1. **Find Session:**
   ```cmd
   dir /b data\sessions\*.json
   ```
   Open the session JSON file to see session ID

2. **Find Audio:**
   ```cmd
   explorer data\audio\AA
   ```
   Audio files are organized by session ID

3. **Find Events:**
   Open `data\events\20251204.jsonl` and search for "AA"

---

## 🎯 What Data is Available?

### Audio Files
- Location: `data/audio/meeting_id/session_id/*.wav`
- Format: WAV files, ~30 seconds each
- Play with: Any media player (double-click)

### Session Data
- Location: `data/sessions/session_id.json`
- Format: JSON
- Contains: Participants, duration, times, status

### Events
- Location: `data/events/YYYYMMDD.jsonl`
- Format: JSON Lines (one JSON per line)
- Contains: All bot actions and meeting events

### Error Screenshots
- Location: `data/error_*.png`
- Format: PNG images
- When: Captured when join fails

---

## ✅ Summary

**Easiest way:**
1. Run `open_data.bat` - opens all folders
2. Or run `python view_data.py` - formatted summary

**Everything is in:** `data/` folder  
**Dashboard:** `http://localhost:8000` for live view

---

**All your data is stored locally and easy to access!** 📁



