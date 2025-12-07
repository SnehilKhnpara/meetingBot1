# 📝 How to Use .env File for Configuration

## 🎯 **Quick Start**

1. **Create `.env` file** by copying the example:
   ```cmd
   cd meetingBot
   copy .env.example .env
   ```

2. **Edit `.env` file** with your preferred text editor (Notepad, VS Code, etc.)

3. **Add/Modify values** as needed (see examples below)

4. **Restart the bot** for changes to take effect

---

## 📋 **Common Configuration Examples**

### **1. Run Browser in Headless Mode (No Window)**

```env
HEADLESS=true
```

### **2. Change Bot Display Name**

```env
BOT_DISPLAY_NAME=My Custom Bot Name
```

### **2b. Set Google Profile Name (For Bot Identification)**

```env
BOT_GOOGLE_PROFILE_NAME=Snehil Khnpara
```

This is the name that appears in Google Meet when the bot is logged in with a Google account. The bot uses this to identify itself in participant lists.

### **3. Allow More Concurrent Meetings**

```env
MAX_CONCURRENT_MEETINGS=10
MAX_CONCURRENT_SESSIONS=20
```

### **4. Change Storage Location**

```env
DATA_DIR=custom_data_folder
PROFILES_ROOT=custom_profiles_folder
```

### **5. Disable Google Login Requirement**

```env
GOOGLE_LOGIN_REQUIRED=false
```

### **6. Use Custom Port**

```env
API_PORT=9000
```

---

## 🔧 **All Available Variables**

### **Server Settings**
- `ENVIRONMENT` - Environment name (default: "dev")
- `API_HOST` - Server host (default: "0.0.0.0")
- `API_PORT` - Server port (default: 8000)

### **Browser Settings**
- `HEADLESS` - Run browser without window (default: "false")
- `PROFILES_ROOT` - Profiles directory (default: "profiles")
- `GMEET_PROFILE_NAME` - Google Meet profile name (default: "google_main")

### **Storage Settings**
- `DATA_DIR` - Data storage directory (default: "data")

### **Authentication**
- `GOOGLE_LOGIN_REQUIRED` - Require Google login (default: "true")

### **Concurrency**
- `MAX_CONCURRENT_MEETINGS` - Max parallel meetings (default: 5)
- `MAX_CONCURRENT_SESSIONS` - Max concurrent sessions (default: 10)
- `SESSION_START_TIMEOUT_SECONDS` - Session start timeout (default: 30)

### **Bot Identity**
- `BOT_DISPLAY_NAME` - Bot's display name (default: "Meeting Bot")
- `BOT_GOOGLE_PROFILE_NAME` - Google profile/account name to identify the bot (e.g., "Snehil Khnpara"). This is the name that appears in Google Meet when logged in with a Google account.

### **Azure (Optional)**
- `AZURE_BLOB_CONNECTION_STRING` - Azure storage connection string
- `AZURE_BLOB_CONTAINER` - Azure container name
- `AZURE_EVENTGRID_ENDPOINT` - Event Grid endpoint URL
- `AZURE_EVENTGRID_KEY` - Event Grid key

### **External Services (Optional)**
- `DIARIZATION_API_URL` - External diarisation service URL

### **Legacy (Optional)**
- `COOKIE_ENCRYPTION_KEY` - Cookie encryption key
- `USE_STORED_COOKIES` - Use stored cookies (default: "false")

---

## 💡 **Tips**

1. **Boolean Values**: Use lowercase `"true"` or `"false"` (with quotes)
2. **Comments**: Lines starting with `#` are ignored
3. **Spaces**: Remove spaces around `=` sign
4. **Quotes**: Usually not needed, but use quotes if value contains spaces
5. **Restart**: Always restart the bot after changing `.env` file

---

## 📝 **Example .env File**

```env
# Browser visible by default
HEADLESS=false

# Bot name
BOT_DISPLAY_NAME=Meeting Assistant

# Allow more meetings
MAX_CONCURRENT_MEETINGS=10

# Custom port
API_PORT=9000

# Custom data folder
DATA_DIR=my_data
```

---

## ✅ **Verification**

After creating/modifying `.env` file:

1. Restart the bot: `start.bat`
2. Check logs to see which values are being used
3. Values from `.env` will override defaults

---

## 🚨 **Important Notes**

- **File Location**: `.env` file must be in the `meetingBot` folder (same location as `start.bat`)
- **File Name**: Must be exactly `.env` (with the dot at the start)
- **Security**: Never commit `.env` file to git (it's already in `.gitignore`)
- **Restart Required**: Changes only take effect after restarting the bot

---

## 🔍 **Troubleshooting**

### **Variables not working?**
- Check file is named exactly `.env` (not `.env.txt`)
- Check file is in the `meetingBot` folder
- Check syntax (no spaces around `=`)
- Restart the bot

### **Can't find .env file?**
- File might be hidden (show hidden files in Windows Explorer)
- Or create it manually in the `meetingBot` folder

---

**Need help?** Check the `.env.example` file for all available options with descriptions!

