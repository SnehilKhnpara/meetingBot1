# 🔐 How to Sign In When Browser Opens

## 🎯 Simple Solution

When the bot opens the browser with the blue Chrome icon, here's what to do:

### Step-by-Step:

1. **Browser opens automatically** - You'll see Chrome/Chromium window

2. **Look for sign-in prompt:**
   - Button that says "Sign in" 
   - Link that says "Sign in to Google"
   - "You can't join" message with sign-in option

3. **Click "Sign in"** and sign in with your Google account

4. **Complete any security steps:**
   - Enter password
   - 2FA if required
   - Security questions if asked

5. **Wait - the bot will detect you signed in!**
   - Bot automatically waits up to 2 minutes
   - It checks every 5 seconds if you've signed in
   - Once signed in, it continues automatically
   - You'll see "✅ Sign-in detected!" in logs

6. **Bot joins the meeting automatically** - No need to do anything else!

---

## 📱 Visual Guide

### What You'll See:

```
┌─────────────────────────────────────┐
│  Chrome Browser (Blue Icon)         │
├─────────────────────────────────────┤
│                                     │
│  Google Meet                        │
│                                     │
│  [Sign in]  ← Click this button     │
│                                     │
│  Or: "You can't join this video     │
│      call" with sign-in link        │
│                                     │
└─────────────────────────────────────┘
```

### After Signing In:

```
┌─────────────────────────────────────┐
│  Chrome Browser                     │
├─────────────────────────────────────┤
│                                     │
│  Google Meet                        │
│                                     │
│  [🎤] [📹]  Join now  ← Should see  │
│                                     │
│  Bot will automatically click       │
│  "Join now" button                  │
│                                     │
└─────────────────────────────────────┘
```

---

## ⏱️ How Long to Wait?

- **Bot waits up to 2 minutes** for you to sign in
- **Checks every 5 seconds** if you've signed in
- **Continues automatically** once signed in
- **You'll see messages** in the dashboard logs:
  - "⚠️ SIGN-IN REQUIRED: Please sign in..."
  - "Still waiting for sign-in... (15/120 seconds)"
  - "✅ Sign-in detected! Continuing..."

---

## ✅ Success Indicators

You'll know it worked when:

✅ Browser shows Google Meet pre-join screen (mic/camera icons)  
✅ Dashboard logs show "✅ Sign-in detected!"  
✅ Dashboard shows "Session joined meeting"  
✅ Status changes to "IN_MEETING"  

---

## ❌ If It Times Out

If you see "Sign-in timeout" after 2 minutes:

1. **Don't close the browser!** Keep it open
2. **Make sure you're signed in** - Check the browser
3. **Try joining again** from the dashboard
4. The browser will reuse your sign-in session

---

## 💡 Pro Tips

### Tip 1: One-Time Setup
- Sign in once manually
- Keep the browser open
- Bot will reuse the session for all meetings
- No need to sign in again!

### Tip 2: Watch the Dashboard
- Open dashboard in another tab
- Watch the "Live Logs" section
- You'll see real-time status updates
- "✅ Sign-in detected!" = success!

### Tip 3: Keep Browser Open
- **Don't close the browser window**
- Browser remembers your sign-in
- Bot can reuse it for future meetings
- Only sign in once!

---

## 🆘 Troubleshooting

### "I don't see a Sign in button"
- Check if you're already signed in
- Look for "Join now" button instead
- Bot should continue automatically

### "I signed in but bot still waiting"
- Make sure you're signed in to the correct Google account
- Try refreshing the page
- Check dashboard logs for details

### "Browser closed automatically"
- Set `HEADLESS=false` to keep browser visible
- Browser shouldn't close on its own
- Check your terminal for errors

---

## 🎯 Quick Summary

1. ✅ Browser opens → Look for "Sign in"
2. ✅ Click it → Sign in with Google account  
3. ✅ Wait → Bot detects automatically (up to 2 min)
4. ✅ Done → Bot joins meeting automatically!

**That's it!** The bot handles everything else. Just sign in when prompted. 🚀




