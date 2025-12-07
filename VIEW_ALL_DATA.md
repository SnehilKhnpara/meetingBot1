# 📊 View ALL Data - Complete Guide

## 🎯 Where to Find Everything

All data from the three Jira stories is stored in the **`data/`** folder:

```
data/
├── audio/              # Audio files (30-second chunks)
│   └── [meeting_id]/
│       └── [session_id]/
│           └── *.wav files
├── events/             # All events (JSON Lines)
│   └── YYYYMMDD.jsonl
└── sessions/           # Meeting summaries (JSON)
    └── [session_id].json
```

---

## 🔍 Quick View - Use the Script

**Easiest way to see everything:**

```cmd
python view_all_data.py
```

This shows:
- ✅ All meeting summaries
- ✅ All participants with join/leave times
- ✅ Active speaker events
- ✅ Participant updates
- ✅ Audio statistics

---

## 📋 Story 1: Audio Capture Data

### Audio Files Location

```
data/audio/[meeting_id]/[session_id]/*.wav
```

**Example:** `data/audio/qrhmzzxzai/0141aace-6568-41e5-8068-8ef981c75c49/`

### View Audio Files

1. **Open folder:**
   ```cmd
   explorer data\audio\[meeting_id]\[session_id]
   ```

2. **Double-click any `.wav` file** to play

3. **Check duration:**
   - Files should be **30 seconds** each
   - If showing 1 second, audio generation needs fixing

### Audio Events

Check events file for audio chunk creation:
```cmd
python view_all_data.py --audio
```

Shows:
- Total audio chunks per meeting
- File locations
- Total size

---

## 📋 Story 2: Participant Tracking Data

### Where It's Stored

1. **Session Files:** `data/sessions/[session_id].json`
   - Contains participant history with join/leave times

2. **Events File:** `data/events/YYYYMMDD.jsonl`
   - Contains `participant_update` events every 30 seconds

### View Participants

**Option 1: Use Script**
```cmd
python view_all_data.py --participants
```

**Option 2: View Session File**
```cmd
notepad data\sessions\[session_id].json
```

**What You'll See:**
```json
{
  "participants": [
    {
      "name": "John Doe",
      "join_time": "2025-12-04T20:00:00+00:00",
      "leave_time": "2025-12-04T20:30:00+00:00",
      "role": "host"
    }
  ]
}
```

### Active Speaker Data

```cmd
python view_all_data.py --speakers
```

Shows:
- Speaker labels
- Confidence scores
- Timestamps for each chunk

---

## 📋 Story 3: Meeting Summary Data

### View Summaries

**Option 1: All Summaries**
```cmd
python view_all_data.py --summary
```

**Option 2: Specific Session**
```cmd
python view_all_data.py --session [session_id]
```

**What's in Each Summary:**
- Meeting ID and platform
- Duration
- All participants (names, join/leave times)
- Total audio chunks
- Start/end times
- Status

---

## 🎯 Complete Data Report

### View Everything for One Meeting

```cmd
python view_all_data.py --session [session_id]
```

Shows:
- ✅ Meeting details
- ✅ All participants with join/leave times
- ✅ Active speaker events
- ✅ Audio chunk count
- ✅ Complete timeline

### View All Meetings

```cmd
python view_all_data.py
```

Shows summary of all meetings with all data.

---

## 📊 Data Summary by Story

### Story 1: Audio Capture
- **Location:** `data/audio/[meeting_id]/[session_id]/*.wav`
- **View:** `python view_all_data.py --audio`
- **Events:** `audio_chunk_created`, `active_speaker`

### Story 2: Participant Tracking
- **Location:** `data/sessions/[session_id].json` (participants field)
- **View:** `python view_all_data.py --participants`
- **Events:** `participant_update` (every 30 seconds)

### Story 3: Meeting Summary
- **Location:** `data/sessions/[session_id].json` (complete summary)
- **View:** `python view_all_data.py --summary`
- **Events:** `meeting_summary` (when meeting ends)

---

## 🔧 Quick Commands

```cmd
REM View all data
python view_all_data.py

REM View only summaries
python view_all_data.py --summary

REM View all participants
python view_all_data.py --participants

REM View active speakers
python view_all_data.py --speakers

REM View audio statistics
python view_all_data.py --audio

REM View complete session report
python view_all_data.py --session [session_id]
```

---

## 📁 Direct File Access

### Open Data Folders

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

## ⚠️ Current Issues to Fix

### Issue 1: Audio Duration (1 second instead of 30)

**Problem:** Audio files are only 1 second long

**Fix Applied:** Updated `src/audio.py` to use 30 seconds

**Next Run:** Audio files should now be 30 seconds each

### Issue 2: Participant Names

**Problem:** Participant extraction may capture UI elements

**Solution:** Enhanced participant tracker is created - will improve name extraction

---

## ✅ All Data is Stored Here

Everything you asked for in the Jira stories is saved:

✅ **Participant tracking** → `data/sessions/[id].json`  
✅ **Join/leave times** → In session JSON  
✅ **Active speaker** → In events and session data  
✅ **Audio chunks** → `data/audio/` folder  
✅ **Meeting summaries** → `data/sessions/[id].json`  
✅ **All events** → `data/events/YYYYMMDD.jsonl`  

---

**Run `python view_all_data.py` to see everything!** 📊



