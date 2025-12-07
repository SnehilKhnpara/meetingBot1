# 🚀 Production-Grade Google Meet Bot Setup

## Overview

This document explains how to set up and use the production-grade Google Meet bot with **persistent authentication** and **automatic profile management** for concurrent meetings.

---

## ✅ Key Features

- ✅ **Persistent Google Login** - Log in once, works forever (even after restart)
- ✅ **Multi-Profile Support** - Run 5-10 meetings in parallel with isolated profiles
- ✅ **Auto-Join Without Approval** - Bot NEVER shows "Ask to join" - joins directly
- ✅ **Automatic Profile Allocation** - Profiles are automatically assigned to sessions
- ✅ **Robust Error Detection** - Detects login failures, cookie expiry, session issues
- ✅ **Screenshot on Failure** - Automatic screenshots when join fails for debugging

---

## 🎯 First-Time Setup

### Step 1: Initial Login (One-Time Per Profile)

The bot uses **persistent browser profiles** to maintain login state. On first run, you need to log in manually.

1. **Set environment variables:**

   ```cmd
   set HEADLESS=false
   set PROFILES_ROOT=profiles
   set GOOGLE_LOGIN_REQUIRED=true
   ```

2. **Start the bot:**

   ```cmd
   start.bat
   ```

3. **Join a test meeting from the dashboard** (`http://localhost:8000`)

4. **When the browser opens:**
   - Sign in to Google with your account
   - Complete 2FA/CAPTCHA if required
   - **Do NOT join the meeting yet** - just ensure you're logged in
   - Close the browser window

5. **The login state is now saved** in `profiles/google_main/` ✅

### Step 2: Verify Login Persists

1. **Restart the bot** (you can now use `HEADLESS=true` if desired)

2. **Join a meeting from the dashboard**

3. **The browser should open already logged in** - no sign-in prompt!

---

## ⚙️ Configuration

### Environment Variables

Add these to your `start.bat` or set them in your environment:

```cmd
REM Profile Management
set PROFILES_ROOT=profiles                    REM Root folder for all profiles
set GMEET_PROFILE_NAME=google_main            REM Default profile name
set GOOGLE_LOGIN_REQUIRED=true                REM Require valid login before joining

REM Concurrency
set MAX_CONCURRENT_MEETINGS=5                 REM Max parallel meetings (each gets own profile)
set MAX_CONCURRENT_SESSIONS=10                REM Overall session limit

REM Browser
set HEADLESS=false                            REM Set to true after initial login
set DATA_DIR=data                              REM Folder for logs, screenshots, etc.
```

### Profile Directory Structure

```
profiles/
├── google_main/          # Main profile (default)
│   ├── Default/          # Browser profile data
│   ├── Cookies           # Google login cookies
│   └── Local State       # Profile metadata
├── google_1/             # Auto-created for concurrent sessions
├── google_2/
└── ...
```

---

## 🔄 How Profile Allocation Works

1. **First meeting** → Uses `profiles/google_main/`

2. **Second meeting** (concurrent) → System checks if `google_main` is available
   - If available → Reuses `google_main`
   - If busy → Creates/uses `profiles/google_1/`

3. **Third meeting** → Allocates next available profile (`google_2`, etc.)

4. **After meeting ends** → Profile is released and available for next session

### Multiple Accounts

To use different Google accounts:

1. **Manually create profiles:**

   ```cmd
   mkdir profiles\account1
   mkdir profiles\account2
   ```

2. **First-time login for each:**
   - Start bot with `GMEET_PROFILE_NAME=account1`
   - Log in with account1 credentials
   - Repeat for account2

3. **The bot will automatically use available profiles** based on which ones are logged in

---

## 🚫 Important: "Ask to Join" Prevention

The bot **NEVER allows "Ask to join"** to appear. If it detects:

- ❌ "Ask to join" button
- ❌ "Still trying to get in..."
- ❌ "Someone will let you in"
- ❌ "You're not allowed"

**The session will FAIL immediately** with a clear error message explaining that:
- The profile is not properly authenticated, OR
- The account doesn't have permission to join this meeting

### Why This Happens

1. **Profile not logged in** → Need to log in manually (see First-Time Setup)
2. **Cookie expired** → Re-login required
3. **Account blocked** → Google detected automation (unlikely with persistent profiles)
4. **Wrong meeting URL** → URL invalid or expired
5. **Host restrictions** → Meeting requires approval (can't be automated)

### Solution

- **Check logs** for the exact error message
- **Check screenshots** in `data/error_*.png`
- **Re-login** if authentication failed
- **Verify meeting URL** is correct and not expired

---

## 📊 Monitoring & Debugging

### Live Logs

View real-time logs in the dashboard:

1. Open `http://localhost:8000`
2. Go to **Live Logs** section
3. Filter by:
   - **Level**: ERROR, WARNING, INFO
   - **Search**: Filter by meeting ID or session ID

### Error Screenshots

When a join fails, screenshots are automatically saved:

```
data/
├── error_<session_id>_<timestamp>.png      # Full page screenshot
└── error_<session_id>_state.json           # Page state (URL, title, error)
```

### Profile Status

Check which profiles are logged in:

```python
from src.google_auth.persistent_profile import get_profile_manager

manager = get_profile_manager()
profiles = manager.list_profiles()

for profile_name in profiles:
    status = manager.get_profile_status(profile_name)
    print(f"{profile_name}: logged_in={status.is_logged_in}, available={status.is_available}")
```

---

## 🔧 Troubleshooting

### "Profile not logged in" Error

**Symptom:** Bot shows "NOT LOGGED IN" error

**Solution:**
1. Stop the bot
2. Set `HEADLESS=false`
3. Start bot and join a meeting
4. Log in manually in the browser window
5. After login, close browser and restart bot

### "Only 'Ask to join' Available" Error

**Symptom:** Bot aborts with this error message

**Causes:**
- Profile authentication is insufficient
- Account doesn't have permission for this meeting
- Meeting requires host approval

**Solution:**
1. **Check profile login:** Verify profile is logged in (see Profile Status)
2. **Try joining manually:** Open the same Meet URL in a normal browser with the same account - do you see "Join now" or "Ask to join"?
3. **If manual join shows "Join now":** Profile needs re-authentication
4. **If manual join shows "Ask to join":** This meeting requires approval - can't be automated

### Multiple Meetings Using Same Profile

**Symptom:** Two meetings conflict or one doesn't join

**Solution:**
- The bot automatically allocates different profiles for concurrent meetings
- Increase `MAX_CONCURRENT_MEETINGS` if needed
- Check logs to see which profiles were allocated

### Cookie Expiry

**Symptom:** Bot was working, now shows login errors

**Solution:**
- Re-authenticate the profile (see "Profile not logged in" solution)
- Persistent profiles should maintain login for months, but Google may require re-auth after:
  - Password change
  - Security alerts
  - Extended inactivity

---

## 🎯 Production Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium

COPY . .

ENV HEADLESS=true
ENV PROFILES_ROOT=/app/profiles
ENV GOOGLE_LOGIN_REQUIRED=true
ENV MAX_CONCURRENT_MEETINGS=5

VOLUME ["/app/profiles", "/app/data"]

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Important:** Mount `profiles/` as a volume to persist login state!

### Kubernetes

```yaml
volumes:
- name: profiles
  persistentVolumeClaim:
    claimName: meeting-bot-profiles
```

---

## 📝 API Usage

### Join Meeting

```bash
POST http://localhost:8000/join-meeting
Content-Type: application/json

{
  "meeting_id": "demo-1",
  "meeting_url": "https://meet.google.com/xxx-yyyy-zzz",
  "platform": "gmeet"
}
```

The bot will:
1. Allocate an available profile
2. Validate login state
3. Join the meeting (bypassing waiting room)
4. Return session ID

### Check Session Status

```bash
GET http://localhost:8000/sessions
```

---

## 🎉 Success Criteria

You know the bot is working correctly when:

1. ✅ **No sign-in prompts** - Browser opens already logged in
2. ✅ **"Join now" button appears** - Not "Ask to join"
3. ✅ **Bot joins automatically** - No waiting room
4. ✅ **Multiple meetings work** - Concurrent sessions use different profiles
5. ✅ **Sessions persist** - After restart, profiles remain logged in

---

## 📚 Architecture

### Components

1. **`PersistentProfileManager`** - Manages profile allocation and status
2. **`EnhancedPlaywrightManager`** - Creates isolated browser contexts per profile
3. **`GoogleMeetJoinFlow`** - Production-grade join logic with error detection
4. **`SessionManager`** - Orchestrates sessions with profile allocation

### Flow

```
Session Request
    ↓
Allocate Profile (google_main or google_N)
    ↓
Create Browser Context (using profile directory)
    ↓
Validate Login State
    ↓
Navigate to Meeting URL
    ↓
Handle Pre-Join Dialogs
    ↓
Join Meeting (bypass waiting room)
    ↓
Validate In Meeting
    ↓
Run Session (audio, participants, etc.)
    ↓
Release Profile
```

---

## 🆘 Support

If you encounter issues:

1. **Check logs** in dashboard or `data/` folder
2. **Review error screenshots** in `data/error_*.png`
3. **Verify profile login** status
4. **Check environment variables** are set correctly

For persistent issues, share:
- Error logs
- Screenshot file
- Profile status output
- Environment configuration

---

## ✅ Checklist

- [ ] Initial login completed in non-headless mode
- [ ] Profile directory created (`profiles/google_main/`)
- [ ] Bot opens already logged in (no sign-in prompt)
- [ ] Bot sees "Join now" (not "Ask to join")
- [ ] Bot joins meeting automatically
- [ ] Multiple concurrent sessions work
- [ ] Logs show no authentication errors
- [ ] Error screenshots captured on failure

---

**🎉 You're all set! The bot is production-ready!**



