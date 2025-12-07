# 🔧 Troubleshooting Guide

## Common Issues and Solutions

### ❌ Session Failed: "Could not find join button"

**Possible causes:**
1. **Meeting requires sign-in** - Google Meet is asking you to sign in
2. **UI changed** - Google Meet updated their interface
3. **Wrong URL** - The meeting URL is invalid or expired

**Solutions:**
- **Sign in manually**: When browser opens, sign in to Google, then try again
- **Check URL**: Make sure the meeting URL is valid and active
- **Check screenshot**: Look at `data/debug_[session_id].png` to see what the page looks like
- **Update selectors**: If Google Meet changed their UI, we may need to update selectors

---

### ❌ Session Failed: "Failed to navigate to meeting URL"

**Possible causes:**
1. **Network timeout** - Slow internet connection
2. **Invalid URL** - URL format is wrong
3. **Meeting doesn't exist** - Meeting was cancelled or expired

**Solutions:**
- Check your internet connection
- Verify the meeting URL is correct
- Try opening the URL manually in a browser first

---

### ❌ Session Failed: "Google Meet requires sign-in"

**Cause:** 
Google Meet requires you to be signed in to a Google account.

**Solutions:**

**Option 1: Sign in manually**
1. When browser opens, sign in to Google
2. Keep the browser open
3. Try joining the meeting again from dashboard

**Option 2: Use cookies (Advanced)**
1. Sign in to Google Meet in a normal browser
2. Export cookies (using browser extension)
3. Load cookies in Playwright (requires code changes)

**Option 3: Use a persistent browser context**
- Save browser profile so you stay signed in
- Requires Playwright context persistence

---

### ❌ Browser opens but doesn't join meeting

**Possible causes:**
1. **Authentication required** - Need to sign in
2. **Waiting room** - Meeting host hasn't let you in
3. **Meeting not started** - Meeting hasn't started yet
4. **Wrong URL** - URL doesn't lead to meeting

**Solutions:**
- **Watch the browser**: See what's happening visually
- **Check for sign-in prompts**: Sign in if needed
- **Check meeting status**: Make sure meeting is active
- **Check URL**: Verify it's the correct meeting link

---

### 🔍 How to Debug

#### 1. Check Logs in Dashboard
- Look at the "Live Logs" section
- Filter for "ERROR" level
- Read the error message carefully

#### 2. Check Screenshots
- Failed sessions save screenshots to `data/debug_[session_id].png`
- Open the screenshot to see what the browser saw
- This helps identify UI issues

#### 3. Watch the Browser
- With `HEADLESS=false`, you can see the browser
- Watch what happens step-by-step
- See if it gets stuck somewhere

#### 4. Check Data Files
- Events: `data/events/YYYYMMDD.jsonl`
- Session data: `data/sessions/[session_id].json`
- Look for error details in these files

---

### ✅ Quick Fixes

**Browser not visible?**
```cmd
set HEADLESS=false
start.bat
```

**Meeting requires sign-in?**
1. Join manually first to sign in
2. Keep browser open
3. Try bot again

**Selectors not working?**
- Google Meet UI changes frequently
- Check screenshot to see current UI
- May need to update selectors in code

---

### 📞 Getting More Help

If you're still having issues:

1. **Check the error message** in logs
2. **Take a screenshot** of the browser window
3. **Check the debug screenshot** in `data/` folder
4. **Share the error details** with support

Common error locations:
- Dashboard logs: Bottom section
- Console logs: Terminal running `uvicorn`
- Session data: `data/sessions/[session_id].json`

---

## 🎯 Most Common Issue: Sign-In Required

**90% of failures are because Google Meet requires sign-in.**

**Quick solution:**
1. Start bot with visible browser (`HEADLESS=false`)
2. When browser opens, manually sign in to Google
3. Don't close browser
4. Try joining meeting again from dashboard
5. Browser will reuse your sign-in session

---

## 📝 Reporting Issues

When reporting issues, include:
- ✅ Error message from logs
- ✅ Screenshot from `data/debug_*.png`
- ✅ Meeting URL format (without sensitive info)
- ✅ Whether browser is visible
- ✅ What you see in the browser window






