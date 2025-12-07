# 🔐 Persistent Sign-In - Join Without Signing In Every Time

## 🎯 Problem Solved

**Before:** Had to sign in to Google every time you join a meeting  
**Now:** Sign in **once**, then bot automatically joins meetings without signing in again!

---

## 🚀 Quick Setup (One-Time)

### Step 1: Set Browser Profile Directory

**Windows:**
```cmd
set BROWSER_PROFILE_DIR=browser_profile
start.bat
```

**Or edit `start.bat`** to add this line before `uvicorn`:
```bat
if not defined BROWSER_PROFILE_DIR set BROWSER_PROFILE_DIR=browser_profile
```

### Step 2: Sign In Once

1. **Start the bot** (with `BROWSER_PROFILE_DIR` set)

2. **Try joining a meeting** from dashboard

3. **When browser opens**, sign in to Google:
   - Click "Sign in"
   - Enter your Google account credentials
   - Complete 2FA if needed

4. **Your sign-in is now saved!** ✅

### Step 3: Enjoy Automatic Joins!

Now when you join meetings:
- ✅ Browser opens
- ✅ **Already signed in** (no sign-in prompt!)
- ✅ Bot joins automatically
- ✅ No more "You can't join" errors

---

## 📁 How It Works

**Browser Profile Directory:**
- Saves all your cookies, login sessions, settings
- Stored in `browser_profile/` folder (or whatever you set)
- **Never expires** (until you delete the folder)
- **One-time setup** - sign in once, works forever!

---

## ⚙️ Configuration

### Set Profile Directory

**Option 1: Environment Variable**
```cmd
set BROWSER_PROFILE_DIR=browser_profile
start.bat
```

**Option 2: Edit `start.bat`**
Add this line before starting uvicorn:
```bat
if not defined BROWSER_PROFILE_DIR set BROWSER_PROFILE_DIR=browser_profile
```

**Option 3: Use Custom Path**
```cmd
set BROWSER_PROFILE_DIR=C:\Users\YourName\meeting_bot_profile
start.bat
```

---

## ✅ Benefits

1. **Sign in once** → Works forever
2. **No more prompts** → Bot joins automatically
3. **Faster joins** → No waiting for sign-in
4. **Same as Chrome** → Uses Chrome's profile system
5. **Secure** → Profile stored locally on your machine

---

## 🔧 How to Use

### First Time (Setup):

1. Set `BROWSER_PROFILE_DIR=browser_profile`
2. Start bot: `start.bat`
3. Join a meeting from dashboard
4. Sign in when browser opens
5. ✅ Done! Sign-in is saved

### Every Time After:

1. Start bot (same profile directory)
2. Join meetings from dashboard
3. **Bot joins automatically** - already signed in! 🎉

---

## 🆘 Troubleshooting

### "Still asking for sign-in"

**Check:**
1. Is `BROWSER_PROFILE_DIR` set?
   ```cmd
   echo %BROWSER_PROFILE_DIR%
   ```
   Should show your profile directory

2. Did you sign in successfully?
   - Make sure you completed full sign-in
   - Check browser window - are you signed in?

3. Is profile directory being used?
   - Check logs for: "Using persistent browser profile"
   - If you don't see this, profile isn't being used

### "Profile directory not working"

**Solution:**
1. Delete the profile folder: `rmdir /s browser_profile`
2. Set `BROWSER_PROFILE_DIR` again
3. Restart bot and sign in fresh

### "Want to switch accounts"

**Solution:**
1. Set different profile directory:
   ```cmd
   set BROWSER_PROFILE_DIR=browser_profile_account2
   ```
2. Sign in with different account
3. Use appropriate profile for each account

---

## 💡 Pro Tips

### Tip 1: Multiple Accounts
Use different profile directories for different Google accounts:
```cmd
# Account 1
set BROWSER_PROFILE_DIR=browser_profile_personal
start.bat

# Account 2  
set BROWSER_PROFILE_DIR=browser_profile_work
start.bat
```

### Tip 2: Backup Profile
The `browser_profile/` folder contains your sign-in session. To backup:
- Copy the entire `browser_profile/` folder
- Restore by copying it back

### Tip 3: Hide Browser After Setup
Once signed in, you can hide the browser:
```cmd
set HEADLESS=true
set BROWSER_PROFILE_DIR=browser_profile
start.bat
```
Bot will still use saved sign-in, but browser stays hidden!

---

## 📋 Step-by-Step Example

```cmd
# 1. Set profile directory
set BROWSER_PROFILE_DIR=browser_profile

# 2. Start bot
start.bat

# 3. Open dashboard: http://localhost:8000

# 4. Join a meeting (any meeting URL)

# 5. Browser opens - SIGN IN HERE (one time only!)

# 6. Bot joins meeting ✅

# 7. Next time - just join, no sign-in needed! 🎉
```

---

## 🎉 That's It!

**One-time setup:**
1. Set `BROWSER_PROFILE_DIR`
2. Sign in once
3. Enjoy automatic joins forever!

No more signing in every time! 🚀




