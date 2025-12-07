# 📊 Complete Data Viewer Guide - All Jira Story Data

## 🎯 Where is ALL Your Data?

All data from the three Jira stories is stored in the **`data/`** folder:

```
data/
├── audio/              # Audio files (30-second chunks)
│   └── [meeting_id]/
│       └── [session_id]/
│           └── *.wav files
├── events/             # All events (JSON Lines)
│   └── YYYYMMDD.jsonl  # One file per day
└── sessions/           # Meeting summaries (JSON)
    └── [session_id].json
```

---

## ⚡ Quick View - All Data at Once

**Run this to see everything:**

```cmd
python view_all_data.py
```

This shows:
- ✅ All meeting summaries with participants
- ✅ Join/leave times for all participants
- ✅ Active speaker events
- ✅ Audio chunk statistics
- ✅ Complete timeline

---

## 📋 Story 1: Audio Capture Data

### Audio Files

**Location:** `data/audio/[meeting_id]/[session_id]/*.wav`

**View Audio Files:**
```cmd
REM Open your audio folder
explorer data\audio\qrhmzzxzai\0141aace-6568-41e5-8068-8ef981c75c49
```

**Check Audio Statistics:**
```cmd
python view_all_data.py --audio
```

### Audio Events in Events File

Check `data/events/20251204.jsonl` for:
- `audio_chunk_created` - Every 30 seconds
- `active_speaker` - Speaker identification for each chunk

**View:**
```cmd
notepad data\events\20251204.jsonl
```

Search for: `"audio_chunk_created"` or `"active_speaker"`

---

## 📋 Story 2: Participant Tracking Data

### Participant Data Location

**1. Session Files:** `data/sessions/[session_id].json`

Contains:
- Participant list
- Join times
- Leave times
- Roles (host/guest)

**2. Events File:** `data/events/YYYYMMDD.jsonl`

Contains:
- `participant_update` events (every 30 seconds)
- Full participant list at each update

### View Participants

**Option 1: Use Script (Recommended)**
```cmd
python view_all_data.py --participants
```

**Option 2: View Session File**
```cmd
notepad data\sessions\212ee1d2-d660-47ad-a9b6-b018faa7aa38.json
```

**What You'll See:**
```json
{
  "participants": [
    {
      "name": "John Doe",
      "join_time": "2025-12-04T20:52:15+00:00",
      "leave_time": "2025-12-04T20:53:50+00:00",
      "role": "host"
    }
  ]
}
```

### Active Speaker Data

**View Active Speakers:**
```cmd
python view_all_data.py --speakers
```

Shows:
- Speaker label for each chunk
- Confidence score
- Timestamp

---

## 📋 Story 3: Meeting Summary Data

### View Meeting Summaries

**All Summaries:**
```cmd
python view_all_data.py --summary
```

**Specific Session:**
```cmd
python view_all_data.py --session 212ee1d2-d660-47ad-a9b6-b018faa7aa38
```

**Complete Report:**
```cmd
python view_all_data.py --session [session_id]
```

### Summary Contains:

- ✅ Meeting ID and platform
- ✅ Session ID
- ✅ Duration (seconds)
- ✅ All participants with join/leave times
- ✅ Total audio chunks
- ✅ Start and end times
- ✅ Status (ended, failed, etc.)

---

## 🔍 Your Current Data

Based on your folder structure:

### Audio Files
- **Meeting:** `qrhmzzxzai`
- **Session:** `0141aace-6568-41e5-8068-8ef981c75c49`
- **Location:** `data/audio/qrhmzzxzai/0141aace-6568-41e5-8068-8ef981c75c49/`
- **Files:** 17 WAV files (one every 30 seconds)

### Session Data
- **Session:** `212ee1d2-d660-47ad-a9b6-b018faa7aa38`
- **Location:** `data/sessions/212ee1d2-d660-47ad-a9b6-b018faa7aa38.json`
- **Duration:** 179 seconds
- **Audio chunks:** 5 chunks
- **Participants:** Tracked in JSON file

---

## 🎯 View All Data Commands

```cmd
REM View everything
python view_all_data.py

REM View meeting summaries
python view_all_data.py --summary

REM View all participants
python view_all_data.py --participants

REM View active speakers
python view_all_data.py --speakers

REM View audio statistics
python view_all_data.py --audio

REM View specific session
python view_all_data.py --session [session_id]
```

---

## 📁 Direct File Access

### Open Folders

```cmd
REM Open main data folder
explorer data

REM Open audio folder
explorer data\audio

REM Open sessions folder  
explorer data\sessions

REM Open events folder
explorer data\events
```

### View JSON Files

Open any `.json` file in:
- Notepad
- VS Code
- Any JSON viewer

---

## ⚠️ Issue: Audio Duration

**Problem:** Audio files are only 1 second (should be 30 seconds)

**Fix Applied:** Updated code to generate 30-second chunks

**After Fix:** New audio files will be 30 seconds each

**Existing Files:** Old files remain 1 second (new ones will be correct)

---

## ✅ All Your Data is Here

Everything from the three Jira stories:

✅ **Story 1:** Audio chunks → `data/audio/`  
✅ **Story 1:** Active speaker events → `data/events/*.jsonl`  
✅ **Story 2:** Participant tracking → `data/sessions/*.json`  
✅ **Story 2:** Join/leave times → In session JSON  
✅ **Story 3:** Meeting summaries → `data/sessions/*.json`  
✅ **Story 3:** All events → `data/events/*.jsonl`  

---

**Run `python view_all_data.py` to see everything in one place!** 📊



