# 🤖 What This Meeting Bot Does

## Quick Summary

This bot **automatically joins video meetings** (Google Meet or Teams), **records audio**, **tracks participants**, **identifies speakers**, and **publishes events** to Azure - all while running **multiple meetings in parallel**.

---

## 📋 Complete Feature List

### ✅ 1. Automated Meeting Joining
- **Automatically joins** Google Meet or Microsoft Teams meetings
- Uses **Playwright** to control a real browser (Chromium)
- **Disables mic/camera** before joining (stays silent/invisible)
- Handles waiting rooms and "Ask to join" prompts
- Works with any valid meeting URL

### ✅ 2. Multi-Meeting Support
- Can join **5-10+ meetings simultaneously**
- Each meeting runs in its own isolated browser session
- Configurable concurrency limit
- No interference between meetings

### ✅ 3. Audio Capture (Every 30 Seconds)
- Records audio in **30-second chunks**
- Uploads each chunk to **Azure Blob Storage**
- File path: `meeting_id/session_id/timestamp.wav`
- Retries on upload failure
- Works across all parallel meetings

### ✅ 4. Speaker Identification
- Analyzes each audio chunk using diarisation service
- Identifies **who is speaking**
- Provides **confidence scores**
- Publishes `active_speaker` events every 30 seconds

### ✅ 5. Participant Tracking
- Monitors **who is in the meeting** every 30 seconds
- Tracks **join times** and **leave times** per participant
- Detects active speaker highlights (if platform exposes)
- Publishes `participant_update` events

### ✅ 6. Auto Exit & Summary
- **Automatically detects** when meeting ends
- **Leaves gracefully** and closes browser session
- Publishes `meeting_summary` event with:
  - Meeting duration
  - Full participant history
  - Number of audio chunks processed
  - All tracked data

### ✅ 7. Azure Integration
- **Blob Storage** for audio files
- **Event Grid** for real-time events:
  - `bot_joined` - Bot started
  - `audio_chunk_created` - New audio ready
  - `active_speaker` - Speaker identified
  - `participant_update` - Participants changed
  - `meeting_summary` - Meeting completed

### ✅ 8. Web Dashboard
- **Beautiful responsive UI** at `http://localhost:8000`
- **Join meetings** via simple form
- **Monitor sessions** in real-time (auto-refreshes)
- **View live logs** with filtering and search
- **Track status** of all meetings

---

## 🔄 Complete Workflow Example

### Step-by-Step:

1. **You Start a Meeting Session**
   ```
   Dashboard: Enter meeting URL → Click "Start Bot Session"
   ```

2. **Bot Joins Meeting**
   ```
   ✅ Opens Chromium browser
   ✅ Navigates to meeting URL
   ✅ Disables mic/camera
   ✅ Clicks "Join now"
   ✅ Enters meeting
   ```

3. **Bot Runs in Background (Every 30 Seconds)**
   ```
   📹 Captures 30s audio → Uploads to Azure Blob
   👥 Scans participant list → Tracks joins/leaves
   🎤 Analyzes audio → Identifies speakers
   📡 Publishes events to Azure Event Grid
   ```

4. **Bot Monitors for End**
   ```
   🔍 Watches for "Meeting ended" / "You left"
   ✅ Auto-leaves when detected
   ```

5. **Bot Publishes Final Summary**
   ```
   📊 Meeting duration: 45 minutes
   👥 Participants: 5 people tracked
   🎵 Audio chunks: 90 chunks (30s each)
   📝 Full participant history with join/leave times
   ```

---

## 💡 Real-World Use Cases

### 1. **Automated Meeting Recording**
- Join meetings automatically
- Record all audio for later transcription
- No human needed to click "Record"

### 2. **Meeting Analytics**
- Track who attended and for how long
- Analyze speaking time per participant
- Generate attendance reports

### 3. **Transcription Service**
- Record audio → Send to transcription service
- Combine with speaker identification
- Generate accurate meeting transcripts

### 4. **Meeting Notes Assistant**
- Record meetings automatically
- Track key speakers
- Generate summaries from audio + events

### 5. **Compliance & Audit**
- Record all meetings for compliance
- Track participant engagement
- Maintain audit trails

### 6. **Virtual Meeting Assistant**
- Join as "silent observer"
- Monitor meetings in real-time
- Provide insights and alerts

---

## 🎯 What Makes It Powerful

1. **Fully Automated** - No manual intervention needed
2. **Scalable** - Run 10+ meetings simultaneously
3. **Reliable** - Handles errors, retries, recovery
4. **Observable** - Full logging and dashboard
5. **Integrable** - Azure-ready, event-driven
6. **Cross-Platform** - Works with Teams and Google Meet

---

## 📊 Architecture Overview

```
┌─────────────────┐
│  Dashboard UI   │  ← You interact here
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI Server │  ← REST API
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Session Manager │  ← Coordinates multiple meetings
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│Meeting1│ │Meeting2│  ← Each runs independently
└───┬────┘ └───┬────┘
    │          │
    └────┬─────┘
         │
    ┌────▼────┐
    │ Playwright│  ← Controls browsers
    └────┬────┘
         │
    ┌────▼────┐
    │ Audio    │  ← Captures & uploads
    │ Tracking │  ← Monitors participants
    │ Events   │  ← Publishes to Azure
    └──────────┘
```

---

## 🚀 Getting Started

1. **Run the bot:**
   ```cmd
   start.bat
   ```

2. **Open dashboard:**
   ```
   http://localhost:8000
   ```

3. **Join a meeting:**
   - Enter Meeting ID
   - Paste meeting URL
   - Select platform (Teams/Meet)
   - Click "Start Bot Session"

4. **Watch it work!** 🎉

---

**That's what this bot does!** It's a complete automated meeting bot system that can handle multiple meetings simultaneously, record everything, track participants, and integrate with Azure services.






