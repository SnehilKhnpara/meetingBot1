# 🐍 Python Not Found - Quick Fix Guide

## ⚡ Quick Solutions

### Option 1: Run the Diagnostic Script (Recommended)

```
Double-click: check_python.bat
```

This script will:
- ✅ Check if Python is installed anywhere on your system
- ✅ Try to find Python in common locations
- ✅ Create a wrapper file if Python is found but not in PATH
- ✅ Give you clear next steps

### Option 2: Install Python (If Not Installed)

```
Double-click: install_python_guide.bat
```

This will show you:
- Step-by-step installation instructions
- Links to download Python
- Options to open Microsoft Store

---

## 📋 Step-by-Step Installation

### Method 1: Microsoft Store (Easiest)

1. **Press Windows key**, type "Microsoft Store"
2. **Search for** "Python 3.11" or "Python 3.12"
3. **Click "Get" or "Install"**
4. Wait for installation
5. **Restart your computer**
6. Run `check_python.bat` to verify

### Method 2: Python.org (Recommended)

1. **Open browser** and go to: https://www.python.org/downloads/
2. **Click** the big yellow "Download Python" button
3. **Run** the downloaded installer (.exe file)
4. **IMPORTANT:** On the first screen, check this box:
   ```
   [x] Add Python to PATH
   ```
5. **Click "Install Now"**
6. Wait for installation
7. **Restart your computer** (important!)
8. Run `check_python.bat` to verify

---

## 🔍 Check if Python is Already Installed

Sometimes Python is installed but not in PATH. Try these:

1. **Open Command Prompt**
2. **Try these commands one by one:**
   ```cmd
   python --version
   python3 --version
   py --version
   ```
3. **If any of them work**, Python is installed but not in PATH

### If Python is Installed But Not in PATH

The `check_python.bat` script will:
- Try to find Python in common locations
- Create a `python.bat` wrapper file automatically
- Allow the bot to work without changing system PATH

---

## ✅ After Installing Python

1. **Restart your computer** (very important!)
2. **Run:** `check_python.bat` to verify installation
3. **Run:** `start.bat` to start the Meeting Bot

---

## 🆘 Still Having Issues?

### Python installed but still getting error?

1. **Check if Python is in PATH:**
   - Open Command Prompt
   - Type: `where python`
   - If nothing appears, Python is not in PATH

2. **Add Python to PATH manually:**
   - Find where Python is installed (usually `C:\Python311\` or `C:\Users\YourName\AppData\Local\Programs\Python\`)
   - Search Windows for "Environment Variables"
   - Click "Edit the system environment variables"
   - Click "Environment Variables"
   - Under "System variables", find "Path" and click "Edit"
   - Click "New" and add Python installation folder
   - Also add: `Python Installation Folder\Scripts`
   - Click OK on all windows
   - **Restart your computer**

3. **Or use the wrapper:**
   - Run `check_python.bat`
   - It will create a `python.bat` wrapper automatically
   - No need to change PATH

---

## 🎯 Quick Commands

```cmd
REM Check if Python works
python --version

REM Run diagnostic
check_python.bat

REM See installation guide
install_python_guide.bat

REM Start bot (after Python is fixed)
start.bat
```

---

## 💡 Tips

- **Always restart** after installing Python
- **Check "Add Python to PATH"** during installation
- **Use Python 3.11 or 3.12** (not 3.10 or older)
- **Run check_python.bat** - it fixes most issues automatically

---

**After Python is working, just run `start.bat` and you're good to go!** 🚀



