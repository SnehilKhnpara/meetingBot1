# ⚡ Quick Start Guide - One-Click Setup

## 🚀 Simplest Way to Start

### Just Double-Click!

**Windows:**
```
Double-click: start.bat
```

**Linux/Mac:**
```bash
./start.sh
```

**That's it!** The script handles everything automatically! 🎉

---

## 📋 What Happens When You Run It

1. ✅ Checks if Python is installed
2. ✅ Creates virtual environment automatically
3. ✅ Installs all dependencies
4. ✅ Detects first-time setup
5. ✅ Shows helpful instructions
6. ✅ Starts the bot server

---

## 🎯 First-Time Setup (One-Time Only)

When you run `start.bat` for the first time:

1. **Script detects it's your first time**
2. **Shows setup instructions**
3. **Press any key to continue**
4. **Open dashboard:** `http://localhost:8000`
5. **Join a test meeting**
6. **Sign in to Google** when browser opens
7. **Close browser** - login saved! ✅

**After this, you're done!** Future runs will be automatic.

---

## ✅ Regular Use (After First Setup)

Just run `start.bat` - that's it!

- Bot opens already logged in
- No setup needed
- Just join meetings from dashboard

---

## 🔧 Optional: Hide Browser After Setup

After first login, you can hide the browser:

1. **Edit `start.bat`**
2. **Find:** `set HEADLESS=false`
3. **Change to:** `set HEADLESS=true`
4. **Save and run** - browser will be hidden!

---

## 📚 Alternative Startup Scripts

- **`start.bat`** - Smart startup (recommended)
- **`start_simple.bat`** - Ultra-simple wrapper
- **`setup_first_time.bat`** - First-time setup wizard

---

## 🆘 Troubleshooting

### "Python not found"
→ Install Python 3.11+ from python.org  
→ Check "Add Python to PATH" during installation

### Script won't start
→ Make sure you're in the project folder  
→ Check file exists: `start.bat` (Windows) or `start.sh` (Linux/Mac)

### Dependencies fail to install
→ Check internet connection  
→ Try manually: `pip install -r requirements.txt`

---

## 🎉 Success!

When you see:
```
Dashboard will be available at: http://localhost:8000
```

**Open that URL and start joining meetings!** 🚀

---

**📖 For detailed setup:** See `PRODUCTION_SETUP.md`  
**📖 For startup details:** See `README_START.md`
