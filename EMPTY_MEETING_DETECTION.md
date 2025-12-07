# 🔍 Empty Meeting Detection - Auto-Leave Feature

## Overview

The bot now automatically detects when **only the bot/user remains** in a meeting and **automatically leaves** to avoid wasting resources.

---

## ✅ How It Works

### Detection Methods

1. **Participant Count Check**
   - Checks People/Participants panel
   - Counts only other participants (excludes "(You)")
   - If count = 0, meeting is empty

2. **UI Message Detection**
   - Looks for "You're the only one" messages
   - Checks for "waiting for others" indicators
   - Detects empty meeting states

3. **Contributors Count**
   - Checks Google Meet "Contributors" section
   - If shows "1" and only "(You)" is listed
   - Triggers empty meeting detection

### Automatic Exit

When detected:
1. ✅ Logs the detection
2. ✅ Captures screenshot (for debugging)
3. ✅ Automatically clicks "Leave" button
4. ✅ Cleans up browser context
5. ✅ Publishes meeting summary

---

## 🎯 Google Meet Detection

### Screenshot Analysis

Based on your screenshot showing:
- People panel shows "1" in Contributors
- Only "Snehil Patel (You)" listed
- No other participants

### Detection Logic

```python
# Check People panel
- Open People panel
- Check "Contributors" count
- If shows "1" and only "(You)" is visible
- → Meeting is empty → Leave automatically
```

### UI Indicators Checked

1. **Text Messages:**
   - "You're the only one"
   - "You are the only one"
   - "Waiting for others"
   - "No one else is here"

2. **Participant Count:**
   - Contributors section showing "1"
   - Only one participant in list (with "(You)")

3. **Panel State:**
   - People panel open
   - Participant list visible
   - Count verified

---

## 🎯 Microsoft Teams Detection

### Detection Methods

1. **Participant Count:**
   - Opens Participants panel
   - Counts valid participants
   - If only 1 (bot/user) → Empty

2. **UI Messages:**
   - "You're the only one"
   - "Waiting for others"

---

## 🔄 Detection Flow

```
Every 30 seconds:
  ├─ Check participant list
  ├─ Count other participants (exclude "(You)")
  ├─ If count = 0:
  │   ├─ Wait 5 seconds
  │   ├─ Check again (confirm)
  │   ├─ If still 0:
  │   │   ├─ Log detection
  │   │   ├─ Capture screenshot
  │   │   ├─ Click Leave button
  │   │   └─ Exit meeting
  │   └─ Else: Continue
  └─ Else: Continue normally
```

---

## ⚙️ Configuration

### Detection Timing

- **Check Interval:** Every 30 seconds (with participant tracking)
- **Confirmation Wait:** 5 seconds before confirming empty
- **Consecutive Checks:** 3 checks (15 seconds) before triggering exit

### Screenshot Capture

Screenshots saved as:
- `data/end_[session_id]_empty_meeting_[timestamp].png`

---

## 📋 What Gets Logged

```json
{
  "event": "empty_meeting_detected",
  "meeting_id": "AA",
  "session_id": "abc-123",
  "reason": "only_bot_remaining",
  "participant_count": 1,
  "other_participants": 0,
  "timestamp": "2025-12-04T20:00:00Z"
}
```

---

## ✅ Benefits

1. **Resource Efficiency**
   - Doesn't waste CPU/network when alone
   - Frees up browser context
   - Releases profile for other meetings

2. **Automatic Cleanup**
   - No manual intervention needed
   - Bot leaves gracefully
   - Summary still published

3. **Clear Logging**
   - Knows exactly why bot left
   - Screenshots for debugging
   - Proper meeting summary

---

## 🐛 Debugging

### If Bot Doesn't Leave

1. **Check Logs:**
   - Look for "empty meeting detected" messages
   - Check participant count in logs

2. **Check Screenshots:**
   - Review `data/end_*_empty_meeting_*.png`
   - Verify participant count visually

3. **Manual Verification:**
   - Open People panel in browser
   - Count participants manually
   - Verify "(You)" indicator

### Common Issues

1. **Participant Count Wrong:**
   - People panel not opening correctly
   - Selectors not matching UI
   - Solution: Check selectors in logs

2. **Detection Too Early:**
   - Participants still joining
   - Solution: Confirmation wait prevents this

3. **Detection Too Late:**
   - Selectors not finding participants
   - Solution: Improved selectors added

---

## 📝 Example Flow

### Scenario: Everyone Leaves

1. **Meeting starts** with 3 participants
2. **2 participants leave**
3. **Bot detects:** Only 1 participant (bot/user)
4. **Bot waits 5 seconds** (confirmation)
5. **Bot checks again:** Still alone
6. **Bot logs:** "Only bot/user remains"
7. **Bot captures screenshot**
8. **Bot clicks "Leave" button**
9. **Bot exits meeting**
10. **Bot publishes summary** with end reason

---

## 🎯 Integration

This feature is integrated into:
- ✅ `src/meeting_end_detector.py` - End detection logic
- ✅ `src/session_manager.py` - Participant loop check
- ✅ Both Google Meet and Teams flows

---

## ✨ Summary

**The bot now automatically detects when you're alone and leaves!**

- ✅ Detects "only bot/user" state
- ✅ Confirms with second check
- ✅ Automatically leaves
- ✅ Captures screenshot
- ✅ Publishes summary

**No more staying in empty meetings!** 🎉



