# 📱 How to Use the Meeting Bot Dashboard UI

## Step-by-Step Guide

### 🎯 Step 1: Start a Bot Session (Join a Meeting)

**In the "Join Meeting" section (left column):**

1. **Enter Meeting ID**
   - Type any identifier (e.g., `demo-1`, `team-meeting`, `abc-123`)
   - This is just a label for you to track the session
   - Example: `my-meeting-1`

2. **Paste Meeting URL**
   - **For Google Meet:** Copy the full URL like:
     ```
     https://meet.google.com/abc-defg-hij
     ```
   - **For Microsoft Teams:** Copy the full meeting link like:
     ```
     https://teams.microsoft.com/l/meetup-join/19%3ameeting...
     ```

3. **Select Platform**
   - Click the dropdown "Select platform..."
   - Choose either:
     - **Google Meet** (if URL starts with `meet.google.com`)
     - **Microsoft Teams** (if URL starts with `teams.microsoft.com`)

4. **Click "Start Bot Session"**
   - The button turns blue when ready
   - Click it to start!

5. **Wait for confirmation**
   - ✅ Success: Green message appears: "✅ Session started! ID: ..."
   - ❌ Error: Red message shows what went wrong

---

### 📊 Step 2: Monitor Your Sessions

**In the "Active Sessions" section (right column):**

You'll see cards showing each bot session:

- **Session ID** - Short identifier
- **UUID** - Full unique ID
- **Status Badge** - Color-coded status:
  - 🟡 **CREATED** - Just queued
  - 🟡 **JOINING** - Bot is opening browser and joining
  - 🟢 **IN_MEETING** - Bot is actively in the meeting
  - ⚪ **ENDED** - Meeting finished normally
  - 🔴 **FAILED** - Something went wrong

- **Platform** - Shows `gmeet` or `teams`
- **Timestamps** - When it started/ended

**Auto-refresh:** Sessions update automatically every 5 seconds

**Manual refresh:** Click the 🔄 Refresh button in top-right of this section

---

### 📝 Step 3: Watch Live Logs

**In the "Live Logs" section (bottom):**

See everything happening in real-time:

1. **Log entries appear automatically**
   - Timestamp (time)
   - Level badge (INFO/WARNING/ERROR)
   - Message text

2. **Filter logs:**
   - **Level dropdown:** Select "INFO", "WARNING", or "ERROR"
   - Select "All Levels" to see everything

3. **Search logs:**
   - Type in "Search logs..." box
   - Search by:
     - Meeting ID
     - Session ID
     - Any text in messages

4. **Clear logs:**
   - Click "Clear" button to wipe the display
   - (Doesn't affect actual bot operations)

---

## 🎬 Complete Example Walkthrough

### Example: Joining a Google Meet Meeting

1. **Get your meeting URL:**
   ```
   https://meet.google.com/xyz-abc-123
   ```

2. **Fill the form:**
   - Meeting ID: `team-standup`
   - Meeting URL: `https://meet.google.com/xyz-abc-123`
   - Platform: Select "Google Meet"
   
3. **Click "Start Bot Session"**

4. **Watch it happen:**
   - In "Active Sessions": New card appears with status "CREATED"
   - Status changes to "JOINING" → "IN_MEETING"
   - In "Live Logs": See messages like:
     - "Session enqueued"
     - "Session starting"
     - "Session joined meeting"
     - "Publishing event"

5. **Bot runs automatically:**
   - Every 30 seconds: Captures audio, tracks participants
   - Logs show: "audio_chunk_created", "participant_update"

6. **When meeting ends:**
   - Status changes to "ENDED"
   - Logs show: "Session ended", "meeting_summary"

---

## 💡 Tips & Tricks

### ✅ Tips for Success:

1. **Use valid meeting URLs**
   - Copy the full URL from the meeting invite
   - Make sure it's a real, active meeting

2. **Check logs for errors**
   - If status shows "FAILED", look in logs for error messages
   - Common issues: Invalid URL, meeting not started, network error

3. **Multiple meetings at once**
   - You can start multiple sessions
   - Each runs independently
   - See all in "Active Sessions"

4. **Refresh if needed**
   - Sessions auto-refresh every 5 seconds
   - Click 🔄 Refresh for instant update

### ⚠️ Common Issues:

**"Invalid meeting URL" error:**
- Make sure URL is complete (full link)
- Check it starts with `https://meet.google.com/` or `https://teams.microsoft.com/`

**Session stuck on "JOINING":**
- Check logs for error messages
- Meeting might require authentication (needs cookies/login)
- Browser might be blocked

**Logs not showing:**
- Clear logs and wait
- Check browser console (F12) for errors
- Make sure server is running

---

## 🎯 Quick Reference

| Action | Location | How |
|--------|----------|-----|
| **Join meeting** | Left column form | Fill form → Click button |
| **View sessions** | Right column | Auto-updates every 5s |
| **See logs** | Bottom section | Scroll down, use filters |
| **Search logs** | Log controls | Type in search box |
| **Filter logs** | Log controls | Select level dropdown |
| **Refresh sessions** | Active Sessions header | Click 🔄 button |
| **Clear logs** | Log controls | Click "Clear" button |

---

## 🚀 That's It!

The UI is designed to be simple:
1. **Fill form** → Join meeting
2. **Watch sessions** → See status
3. **Check logs** → Monitor activity

Everything else happens automatically! 🎉






