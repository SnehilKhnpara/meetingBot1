# 🚀 One-Click Startup Guide

## 🎯 Simplest Way to Start

### Windows Users

**Just double-click one of these files:**

1. **`start.bat`** - Smart startup with automatic setup
   - Detects first-time setup
   - Creates virtual environment if needed
   - Installs dependencies automatically
   - Shows helpful instructions

2. **`start_simple.bat`** - Ultra-simple (just runs start.bat)

3. **`setup_first_time.bat`** - First-time setup wizard
   - Guides you through initial login
   - Removes old profiles if needed

### Linux/Mac Users

```bash
chmod +x start.sh
./start.sh
```

---

## ⚡ Quick Start (3 Steps)

### Step 1: Run the Script

**Windows:**
```
Double-click start.bat
```

**Linux/Mac:**
```bash
./start.sh
```

### Step 2: First-Time Login (If Needed)

If it's your first time:
1. Script will detect and show instructions
2. Open dashboard: `http://localhost:8000`
3. Join a test meeting
4. **Sign in to Google** when browser opens
5. Close browser - done! ✅

### Step 3: Use the Bot

That's it! Just join meetings from the dashboard. The bot will:
- ✅ Open already logged in
- ✅ Join automatically (no "Ask to join")
- ✅ Handle multiple meetings

---

## 🔧 What the Script Does Automatically

1. ✅ Checks Python installation
2. ✅ Creates virtual environment if needed
3. ✅ Installs all dependencies
4. ✅ Installs Playwright Chromium
5. ✅ Detects first-time setup
6. ✅ Sets optimal defaults
7. ✅ Shows clear instructions

---

## 📋 Configuration (Optional)

The script sets these defaults automatically:

- `HEADLESS=false` (visible browser - can change after first login)
- `PROFILES_ROOT=profiles`
- `GOOGLE_LOGIN_REQUIRED=true`
- `MAX_CONCURRENT_MEETINGS=5`

**To customize:** Edit `start.bat` (Windows) or `start.sh` (Linux/Mac)

---

## 🎯 After First Login

Once you're logged in, you can:

1. **Hide the browser** (optional):
   - Edit `start.bat` → Change `HEADLESS=false` to `HEADLESS=true`
   - Or set environment variable: `set HEADLESS=true`

2. **Just run `start.bat`** - no setup needed anymore!

---

## 🆘 Troubleshooting

### "Python not found"
- Install Python 3.11+ from python.org
- Make sure to check "Add Python to PATH" during installation

### "Dependencies failed to install"
- Check internet connection
- Try running manually: `pip install -r requirements.txt`

### Script won't run
- Make sure you're in the project directory
- Check file permissions (Linux/Mac): `chmod +x start.sh`

---

## ✅ Success!

When you see:
```
Dashboard will be available at: http://localhost:8000
```

**You're ready!** Open the dashboard and start joining meetings! 🎉

---

**That's it! One click (or double-click) and you're running!**



