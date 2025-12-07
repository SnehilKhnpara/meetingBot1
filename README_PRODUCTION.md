# 🤖 Production-Grade Meeting Bot

A production-ready meeting bot that automatically joins Google Meet and Microsoft Teams meetings with persistent authentication, multi-profile support, and robust error handling.

## ✨ Key Features

- ✅ **Persistent Google Login** - Log in once, works forever (even after restart)
- ✅ **Multi-Profile Support** - Run 5-10 meetings in parallel with isolated profiles  
- ✅ **Auto-Join Without Approval** - Never shows "Ask to join" - joins directly
- ✅ **Automatic Profile Allocation** - Profiles automatically assigned to sessions
- ✅ **Robust Error Detection** - Detects login failures, cookie expiry, session issues
- ✅ **Screenshot on Failure** - Automatic screenshots when join fails for debugging
- ✅ **Production Ready** - Container-friendly, memory efficient, scalable

---

## 🚀 Quick Start

### 1. First-Time Login (One-Time Setup)

```cmd
set HEADLESS=false
set GOOGLE_LOGIN_REQUIRED=true
start.bat
```

1. Open dashboard: `http://localhost:8000`
2. Join a test meeting
3. **Sign in to Google** in the browser window
4. Close browser - login saved! ✅

### 2. Use the Bot

```cmd
set HEADLESS=true  REM Optional - hide browser
start.bat
```

Join meetings from dashboard - bot opens already logged in!

---

## 📚 Documentation

- **[QUICK_START.md](QUICK_START.md)** - Get running in 5 minutes
- **[PRODUCTION_SETUP.md](PRODUCTION_SETUP.md)** - Complete setup guide
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Technical architecture

---

## ⚙️ Configuration

### Environment Variables

```cmd
set PROFILES_ROOT=profiles                    REM Profile storage location
set GMEET_PROFILE_NAME=google_main            REM Default profile name
set GOOGLE_LOGIN_REQUIRED=true                REM Require valid login
set MAX_CONCURRENT_MEETINGS=5                 REM Max parallel meetings
set HEADLESS=false                            REM Browser visibility
```

---

## 🎯 Architecture

### Core Components

1. **`PersistentProfileManager`** - Manages profile allocation and status
2. **`EnhancedPlaywrightManager`** - Creates isolated browser contexts per profile
3. **`GoogleMeetJoinFlow`** - Production-grade join logic with error detection
4. **`SessionManager`** - Orchestrates sessions with profile allocation

### Flow

```
Session Request → Allocate Profile → Create Context → Validate Login 
→ Join Meeting (bypass waiting room) → Run Session → Release Profile
```

---

## 🚫 "Ask to Join" Prevention

The bot **NEVER allows "Ask to join"** to appear. If detected:

- ❌ Session fails immediately
- ✅ Clear error message explaining why
- 📸 Screenshot captured for debugging

**Causes:**
- Profile not logged in → Re-login required
- Cookie expired → Re-authentication needed
- Account blocked → Google detected automation (rare)
- Wrong meeting URL → URL invalid/expired

---

## 🔧 Troubleshooting

### Profile Not Logged In
**Solution:** Set `HEADLESS=false`, start bot, log in manually, restart

### "Ask to Join" Error
**Solution:** Profile authentication failed - re-login required

### Multiple Meetings Conflict
**Solution:** Check `MAX_CONCURRENT_MEETINGS` setting

**📖 See [PRODUCTION_SETUP.md](PRODUCTION_SETUP.md) for detailed troubleshooting**

---

## 📊 Monitoring

- **Dashboard:** `http://localhost:8000` - Live logs, session status
- **Error Screenshots:** `data/error_*.png` - Automatic on failure
- **Profile Status:** Check logs for allocation messages

---

## 🐳 Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt && playwright install chromium
ENV HEADLESS=true GOOGLE_LOGIN_REQUIRED=true
VOLUME ["/app/profiles", "/app/data"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Important:** Mount `profiles/` as volume to persist login!

---

## ✅ Success Criteria

- ✅ No sign-in prompts - Browser opens already logged in
- ✅ "Join now" appears - Never "Ask to join"
- ✅ Bot joins automatically - No waiting room
- ✅ Multiple meetings work - Concurrent sessions use different profiles
- ✅ Sessions persist - After restart, profiles remain logged in

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

---

## 🎉 Ready for Production!

The bot is production-grade and ready for deployment. See documentation for detailed setup and troubleshooting.

**Questions?** Check the documentation files or review error logs/screenshots.



