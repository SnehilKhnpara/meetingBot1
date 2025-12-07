# 📝 How to Add Values to .env File

## 🎯 **Quick Steps**

### **Step 1: Create .env File**

**Windows:**
1. Open Notepad or any text editor
2. Save the file as `.env` (with the dot at the start)
3. Make sure to save it in the `meetingBot` folder (same location as `start.bat`)

**Or use Command Prompt:**
```cmd
cd meetingBot
echo. > .env
```

---

### **Step 2: Add Your Values**

Open the `.env` file and add your configuration. Here's the format:

```env
VARIABLE_NAME=value
```

**Examples:**

```env
# Run browser in headless mode (no window)
HEADLESS=true

# Change bot name
BOT_DISPLAY_NAME=My Bot Name

# Allow more concurrent meetings
MAX_CONCURRENT_MEETINGS=10

# Use custom port
API_PORT=9000
```

---

## 📋 **All Available Variables**

### **Browser Settings**
```env
HEADLESS=false              # true = no window, false = show window
PROFILES_ROOT=profiles      # Folder for browser profiles
GMEET_PROFILE_NAME=google_main
```

### **Storage**
```env
DATA_DIR=data              # Folder for storing data
```

### **Authentication**
```env
GOOGLE_LOGIN_REQUIRED=true  # Require Google login
```

### **Concurrency**
```env
MAX_CONCURRENT_MEETINGS=5   # Max parallel meetings
MAX_CONCURRENT_SESSIONS=10  # Max concurrent sessions
SESSION_START_TIMEOUT_SECONDS=30
```

### **Bot Identity**
```env
BOT_DISPLAY_NAME=Meeting Bot
```

### **Server**
```env
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=dev
```

### **Azure (Optional)**
```env
AZURE_BLOB_CONNECTION_STRING=your_connection_string
AZURE_BLOB_CONTAINER=container_name
AZURE_EVENTGRID_ENDPOINT=https://...
AZURE_EVENTGRID_KEY=your_key
```

### **External Services (Optional)**
```env
DIARIZATION_API_URL=https://your-service.com/api/analyze
```

---

## 📝 **Complete Example .env File**

Copy this entire content into your `.env` file:

```env
# Browser Configuration
HEADLESS=false
PROFILES_ROOT=profiles
GMEET_PROFILE_NAME=google_main

# Storage
DATA_DIR=data

# Authentication
GOOGLE_LOGIN_REQUIRED=true

# Concurrency
MAX_CONCURRENT_MEETINGS=5
MAX_CONCURRENT_SESSIONS=10
SESSION_START_TIMEOUT_SECONDS=30

# Bot Identity
BOT_DISPLAY_NAME=Meeting Bot
BOT_GOOGLE_PROFILE_NAME=Snehil Khnpara

# Server
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=dev
```

---

## ⚠️ **Important Rules**

1. **No spaces** around the `=` sign:
   ```env
   ✅ HEADLESS=false
   ❌ HEADLESS = false
   ```

2. **Boolean values** use lowercase:
   ```env
   ✅ HEADLESS=true
   ❌ HEADLESS=TRUE
   ```

3. **No quotes** needed (usually):
   ```env
   ✅ BOT_DISPLAY_NAME=My Bot
   ✅ BOT_DISPLAY_NAME="My Bot"  # Also works
   ```

4. **Comments** start with `#`:
   ```env
   # This is a comment
   HEADLESS=false
   ```

5. **File location**: Must be in `meetingBot` folder (same as `start.bat`)

---

## 🔄 **After Adding Values**

1. **Save** the `.env` file
2. **Restart** the bot (`start.bat`)
3. Changes will take effect automatically!

---

## 💡 **Common Use Cases**

### **Hide Browser Window**
```env
HEADLESS=true
```

### **Change Bot Name**
```env
BOT_DISPLAY_NAME=Assistant Bot
```

### **More Parallel Meetings**
```env
MAX_CONCURRENT_MEETINGS=10
```

### **Custom Port**
```env
API_PORT=9000
```

### **Custom Data Folder**
```env
DATA_DIR=my_custom_data
```

---

## 🚨 **Troubleshooting**

### **File not working?**
- ✅ Check file name is exactly `.env` (with dot at start)
- ✅ Check file is in `meetingBot` folder
- ✅ Check no spaces around `=` sign
- ✅ Restart the bot after changes

### **Can't see .env file?**
- It might be hidden (files starting with `.` are often hidden)
- In Windows Explorer: View → Show → Hidden items

### **Variables not applying?**
- Make sure you restarted the bot
- Check for typos in variable names
- Check the file is saved correctly

---

## 📍 **File Location**

Your `.env` file should be here:
```
D:\Projects\Meeting Bot\meetingBot\.env
```

Same folder as:
- `start.bat`
- `requirements.txt`
- `src/` folder

---

**Need help?** Check `HOW_TO_USE_ENV.md` for more detailed examples!

