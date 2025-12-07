# 📍 Where is ALL Your Data?

## 🎯 Quick Answer

**ALL your data is in the `data/` folder!**

Run this to see everything:
```cmd
python view_complete_data.py
```

---

## 📂 Folder Structure

```
data/
├── audio/              ← Audio files (WAV)
│   └── [meeting_id]/
│       └── [session_id]/
│           └── *.wav
├── events/             ← All events (JSON Lines)
│   └── 20251204.jsonl
└── sessions/           ← Meeting summaries (JSON)
    └── [session_id].json
```

---

## 📊 Story 1: Audio Capture Data

### ✅ Audio Files

**Location:** `data/audio/[meeting_id]/[session_id]/*.wav`

**Your Files:**
- `data/audio/qrhmzzxzai/0141aace-6568-41e5-8068-8ef981c75c49/`
- 17 WAV files (one every 30 seconds)

**View:**
```cmd
explorer data\audio\qrhmzzxzai\0141aace-6568-41e5-8068-8ef981c75c49
```

**Issue:** Current files are 1 second (should be 30 seconds)
**Fix:** Code updated - new files will be 30 seconds ✅

### ✅ Active Speaker Events

**Location:** `data/events/20251204.jsonl`

Look for: `"event_type": "active_speaker"`

**View:**
```cmd
notepad data\events\20251204.jsonl
```

Or use script:
```cmd
python view_all_data.py --speakers
```

---

## 📊 Story 2: Participant Tracking Data

### ✅ Participant List with Join/Leave Times

**Location:** `data/sessions/[session_id].json`

**Your Session:**
- `data/sessions/212ee1d2-d660-47ad-a9b6-b018faa7aa38.json`

**Contains:**
- Participant names
- Join times
- Leave times
- Roles (host/guest)

**View:**
```cmd
notepad data\sessions\212ee1d2-d660-47ad-a9b6-b018faa7aa38.json
```

Or use script:
```cmd
python view_complete_data.py --session 212ee1d2-d660-47ad-a9b6-b018faa7aa38
```

### ✅ Participant Update Events

**Location:** `data/events/20251204.jsonl`

Look for: `"event_type": "participant_update"`

Updated **every 30 seconds** with full participant list.

**View:**
```cmd
python view_all_data.py --participants
```

---

## 📊 Story 3: Meeting Summary Data

### ✅ Complete Meeting Summary

**Location:** `data/sessions/[session_id].json`

**Your Session Summary Contains:**
- Meeting ID: `qrhmzzxzai`
- Platform: `gmeet`
- Duration: 179 seconds
- Participants: 4 tracked
- Audio chunks: 5 chunks
- Start time: `2025-12-04T20:51:32`
- End time: `2025-12-04T20:54:31`
- Status: `ended`

**View:**
```cmd
python view_complete_data.py --session 212ee1d2-d660-47ad-a9b6-b018faa7aa38
```

---

## 🔍 Quick Access Commands

### View Everything
```cmd
python view_complete_data.py
```

### View Specific Session
```cmd
python view_complete_data.py --session 212ee1d2-d660-47ad-a9b6-b018faa7aa38
```

### View All Participants
```cmd
python view_all_data.py --participants
```

### View Audio Statistics
```cmd
python view_all_data.py --audio
```

### Open Data Folders
```cmd
explorer data
explorer data\audio
explorer data\sessions
explorer data\events
```

---

## ⚠️ Issues to Fix

### Issue 1: Audio Files Only 1 Second

**Problem:** Audio files are 1 second instead of 30 seconds

**Fix:** ✅ Code updated - new files will be 30 seconds

**Old Files:** Will remain 1 second (already created)

**New Files:** Will be 30 seconds each ✅

### Issue 2: Participant Names

**Problem:** Some participant names look like UI elements:
- "Backgrounds and effects"
- "Your microphone is off"

**Cause:** Participant extraction picking up UI elements

**Fix Needed:** Improve participant name filtering

---

## 📋 What Data You Have

### From Your Session (212ee1d2...)

✅ **Meeting:** qrhmzzxzai  
✅ **Duration:** 179 seconds (3 minutes)  
✅ **Participants:** 4 tracked  
✅ **Audio chunks:** 5 chunks  
✅ **Events:** All saved in events file  

### All Data Locations

✅ **Audio files:** `data/audio/qrhmzzxzai/0141aace-.../`  
✅ **Session summary:** `data/sessions/212ee1d2-...json`  
✅ **All events:** `data/events/20251204.jsonl`  

---

## 🎯 View All Data Now

**Run this command:**

```cmd
python view_complete_data.py --session 212ee1d2-d660-47ad-a9b6-b018faa7aa38
```

This will show:
- ✅ Complete meeting summary
- ✅ All participants with join/leave times
- ✅ Audio chunk information
- ✅ Active speaker events
- ✅ All events timeline

---

**All your data is in the `data/` folder!** 📁



