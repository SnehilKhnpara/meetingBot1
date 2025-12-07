# 🚨 QUICK FIX: Port 8000 Already in Use

## The Problem

Port 8000 is already being used by another process (likely a previous bot instance).

---

## ✅ **EASIEST SOLUTION**

### **Option 1: Kill the Process (Recommended)**

Run this command in a **new** Command Prompt window:

```cmd
taskkill /F /PID 2004
```

Then run `start.bat` again.

---

### **Option 2: Use the Helper Script**

I've created a script for you. Run this:

```cmd
cd "D:\Projects\Meeting Bot\meetingBot"
kill_port_8000.bat
```

This will automatically find and kill any process using port 8000.

Then run `start.bat` again.

---

### **Option 3: Change the Port**

Edit your `.env` file (or create it) and add:

```env
API_PORT=8001
```

Then access the dashboard at: `http://localhost:8001` instead of `http://localhost:8000`

---

## 🔧 **Manual Method**

1. **Open Task Manager** (Ctrl+Shift+Esc)
2. **Find Python processes**
3. **End any Python processes** that look like they're running the bot
4. **Run `start.bat` again**

---

**Quickest fix:** Run `kill_port_8000.bat` then `start.bat`!

