# ✅ BOT_GOOGLE_PROFILE_NAME - Setup Guide

## 🎯 **What is This?**

`BOT_GOOGLE_PROFILE_NAME` is an environment variable that tells the bot what Google account name to look for when identifying itself in Google Meet participant lists.

When you log in to Google Meet with a Google account (like "Snehil Khnpara"), the bot needs to know this name so it can:
- ✅ Recognize itself in the participant list
- ✅ Only leave when it's truly alone
- ✅ Distinguish between real users and itself

---

## 📝 **How to Set It**

### **Step 1: Create/Edit .env File**

Create or edit the `.env` file in the `meetingBot` folder:

**Location:** `D:\Projects\Meeting Bot\meetingBot\.env`

### **Step 2: Add the Variable**

Add this line to your `.env` file:

```env
BOT_GOOGLE_PROFILE_NAME=Snehil Khnpara
```

**Important:**
- Use the exact name that appears in Google Meet when you're logged in
- The name should match what shows in the participant list
- Case doesn't matter (it's case-insensitive)

---

## 🔍 **How to Find Your Google Profile Name**

1. **Join a Google Meet** with the same Google account you use for the bot
2. **Open the People panel** (click the People icon)
3. **Look at your name** - it should show something like:
   - "Snehil Khnpara (You)"
   - "Snehil Khnpara"
   - Your Google account display name

4. **Use that name** (without the "(You)" part) in the `.env` file

---

## ✅ **Complete .env Example**

Here's a complete example with all bot identification variables:

```env
# Bot Identity
BOT_DISPLAY_NAME=Meeting Bot
BOT_GOOGLE_PROFILE_NAME=Snehil Khnpara

# Browser Settings
HEADLESS=false
PROFILES_ROOT=profiles
GMEET_PROFILE_NAME=google_main

# Storage
DATA_DIR=data

# Other settings...
MAX_CONCURRENT_MEETINGS=5
```

---

## 🎯 **How It Works**

When the bot joins a meeting:

1. **Extracts participant names** from Google Meet
2. **Checks each name** against:
   - `BOT_GOOGLE_PROFILE_NAME` (your Google account name)
   - `BOT_DISPLAY_NAME` (default: "Meeting Bot")
   - Names with "(You)" suffix
3. **Identifies itself** using these names
4. **Only leaves** when no real participants remain

---

## 📋 **Examples**

### **Example 1: Basic Setup**
```env
BOT_GOOGLE_PROFILE_NAME=Snehil Khnpara
```

### **Example 2: With Bot Display Name**
```env
BOT_DISPLAY_NAME=Meeting Assistant
BOT_GOOGLE_PROFILE_NAME=Snehil Khnpara
```

### **Example 3: Multiple Names (for different accounts)**
The bot will check both names, so you can set:
```env
BOT_DISPLAY_NAME=Meeting Bot
BOT_GOOGLE_PROFILE_NAME=Snehil Khnpara
```

If you use multiple Google accounts, the bot will recognize itself with either name.

---

## ⚠️ **Important Notes**

1. **Name Matching:**
   - Matching is **case-insensitive**
   - Partial matches work (e.g., "Snehil" matches "Snehil Khnpara")
   - The "(You)" suffix is automatically detected

2. **Name Changes:**
   - If you change your Google account name, update this variable
   - Restart the bot after changing the `.env` file

3. **Multiple Accounts:**
   - Each profile can have a different Google account name
   - Set the name that matches the account used in that profile

---

## 🔄 **After Setting Up**

1. **Save** the `.env` file
2. **Restart** the bot (`start.bat`)
3. **Test** by joining a meeting
4. **Check logs** to see if bot identification is working

---

## 🚨 **Troubleshooting**

### **Bot not recognizing itself?**

1. ✅ Check the name in `.env` matches exactly what appears in Google Meet
2. ✅ Make sure `.env` file is in the `meetingBot` folder
3. ✅ Restart the bot after changing `.env`
4. ✅ Check logs for bot identification messages

### **Name appears differently?**

Google Meet might show:
- Full name: "Snehil Khnpara"
- First name only: "Snehil"
- With suffix: "Snehil Khnpara (You)"

The bot handles all of these automatically!

---

## 📝 **Code Reference**

This variable is used in:
- `src/config.py` - Settings definition
- `src/session_manager.py` - Bot identification logic
- `get_bot_identifiers()` function - Returns list of bot names to check

---

**Status**: ✅ **CONFIGURED**

The bot will now use "Snehil Khnpara" to identify itself in Google Meet!

