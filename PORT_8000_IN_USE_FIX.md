# ✅ Port 8000 Already in Use - Fix Guide

## 🔴 **Problem**

You're seeing this error:
```
ERROR: [Errno 10048] error while attempting to bind on address ('0.0.0.0', 8000): 
only one usage of each socket address (protocol/network address/port) is normally permitted
```

This means **another instance of the bot is already running** on port 8000.

---

## ✅ **Solution Options**

### **Option 1: Kill the Existing Process (Recommended)**

**Quick Fix - Run this command:**
```cmd
taskkill /F /PID 2004
```

**Or use the helper script I created:**
```cmd
kill_port_8000.bat
```

This will automatically find and kill any process using port 8000.

---

### **Option 2: Change the Port**

You can use a different port by setting `API_PORT` in your `.env` file:

1. **Create/edit `.env` file** in the `meetingBot` folder
2. **Add this line:**
   ```env
   API_PORT=8001
   ```
3. **Save and restart** the bot

Then access the dashboard at: `http://localhost:8001`

---

### **Option 3: Find and Close the Other Instance**

1. **Open Task Manager** (Ctrl+Shift+Esc)
2. **Look for Python processes**
3. **End any Python processes** that might be running the bot
4. **Or close any other terminal windows** that might have the bot running

---

## 🚀 **Quick Fix Steps**

1. **Stop the existing process:**
   ```cmd
   cd meetingBot
   kill_port_8000.bat
   ```

2. **Then start the bot again:**
   ```cmd
   start.bat
   ```

---

## 🔍 **Check What's Using Port 8000**

To see what process is using port 8000:
```cmd
netstat -ano | findstr :8000
```

This will show the Process ID (PID) - you can kill it with:
```cmd
taskkill /F /PID <PID>
```

---

## 💡 **Prevention**

To avoid this in the future:
- **Always close the bot properly** (Press Ctrl+C)
- **Check if it's already running** before starting again
- **Use a different port** if you need to run multiple instances

---

**Status**: ✅ **FIXED** - Use one of the solutions above!

