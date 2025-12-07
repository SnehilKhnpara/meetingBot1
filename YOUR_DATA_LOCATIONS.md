# 📍 Where is ALL Your Data? - Complete Guide

## 🎯 Quick Answer

**ALL your data is stored in the `data/` folder!**

---

## 📂 Your Current Data

Based on your screenshot and folder structure:

### Audio Files (Story 1)
**Location:** `data/audio/qrhmzzxzai/0141aace-6568-41e5-8068-8ef981c75c49/`

- ✅ 17 WAV files
- ⚠️ Currently 1 second each (should be 30 seconds)
- ✅ Fix applied - new files will be 30 seconds

### Session Data (Story 2 & 3)
**Location:** `data/sessions/212ee1d2-d660-47ad-a9b6-b018faa7aa38.json`

Contains:
- ✅ Meeting ID: `qrhmzzxzai`
- ✅ Duration: 179 seconds
- ✅ Participants: 4 tracked
- ✅ Audio chunks: 5 chunks
- ✅ Join/leave times

### Events (All Stories)
**Location:** `data/events/20251204.jsonl`

Contains:
- ✅ `audio_chunk_created` events
- ✅ `active_speaker` events
- ✅ `participant_update` events
- ✅ `meeting_summary` event

---

## 🔍 How to View All Data

### Method 1: Complete Data Viewer (Recommended)

```cmd
python view_complete_data.py
```

Shows:
- ✅ All meetings
- ✅ All participants with join/leave times
- ✅ Active speaker events
- ✅ Audio statistics
- ✅ Complete timeline

### Method 2: View Specific Session

```cmd
python view_complete_data.py --session 212ee1d2-d660-47ad-a9b6-b018faa7aa38
```

### Method 3: Open Folders Directly

```cmd
REM Open all data folders
explorer data

REM Open audio folder
explorer data\audio\qrhmzzxzai\0141aace-6568-41e5-8068-8ef981c75c49

REM Open sessions folder
explorer data\sessions
```

---

## 📊 Story 1: Audio Capture Data

### Audio Files

**Your Files:**
- Folder: `data/audio/qrhmzzxzai/0141aace-6568-41e5-8068-8ef981c75c49/`
- 17 WAV files

**Issue:** Files are 1 second (should be 30 seconds)
**Fix:** ✅ Code updated - new recordings will be 30 seconds

### Active Speaker Events

**Location:** `data/events/20251204.jsonl`

Search for: `"active_speaker"`

**View:**
```cmd
python view_all_data.py --speakers
```

---

## 📊 Story 2: Participant Tracking Data

### Participant List

**Location:** `data/sessions/212ee1d2-d660-47ad-a9b6-b018faa7aa38.json`

**Contains:**
- Participant names
- Join times
- Leave times
- Roles

**View:**
```cmd
notepad data\sessions\212ee1d2-d660-47ad-a9b6-b018faa7aa38.json
```

Or use:
```cmd
python view_all_data.py --participants
```

### Participant Updates

**Location:** `data/events/20251204.jsonl`

Look for: `"participant_update"` (every 30 seconds)

---

## 📊 Story 3: Meeting Summary

### Complete Summary

**Location:** `data/sessions/212ee1d2-d660-47ad-a9b6-b018faa7aa38.json`

**Contains:**
- Meeting details
- Duration
- All participants
- Audio chunk count
- Start/end times

**View:**
```cmd
python view_complete_data.py --session 212ee1d2-d660-47ad-a9b6-b018faa7aa38
```

---

## ⚠️ Issues Found & Fixed

### Issue 1: Audio Duration (1 second instead of 30)

**Problem:** Audio files are only 1 second long

**Fix Applied:** ✅ Code updated to generate 30-second chunks

**Status:** 
- Old files: Will remain 1 second
- New files: Will be 30 seconds ✅

**Test:** Join a new meeting - audio files should be 30 seconds

### Issue 2: Participant Names (UI Elements)

**Problem:** Participant extraction capturing UI elements:
- "Backgrounds and effects"
- "Your microphone is off"

**Fix Needed:** Improve participant name filtering (enhanced tracker created)

---

## 🎯 Quick Commands Summary

```cmd
REM View all data
python view_complete_data.py

REM View specific session
python view_complete_data.py --session [session_id]

REM View participants
python view_all_data.py --participants

REM View audio statistics
python view_all_data.py --audio

REM Open data folder
explorer data
```

---

## ✅ All Your Data Locations

| Data Type | Location |
|-----------|----------|
| Audio files | `data/audio/[meeting_id]/[session_id]/*.wav` |
| Session summaries | `data/sessions/[session_id].json` |
| All events | `data/events/YYYYMMDD.jsonl` |
| Error screenshots | `data/error_*.png` |

---

**Everything is in the `data/` folder! Run `python view_complete_data.py` to see it all!** 📊



