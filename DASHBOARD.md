# 🎯 Meeting Bot Dashboard Guide

## ✨ What's New

You now have a **beautiful, responsive web dashboard** to manage your meeting bot!

### Features

1. **Join Meeting Form** - Simple UI to start bot sessions
2. **Live Session Monitoring** - See all active sessions with real-time status updates
3. **Live Logs Viewer** - Filter, search, and view all system logs in real-time
4. **Responsive Design** - Works on desktop, tablet, and mobile

---

## 🚀 Quick Start

### Option 1: Easy Start (Recommended)

**Windows:**
```cmd
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

### Option 2: Manual Start

```bash
# Activate venv
.\.venv\Scripts\activate  # Windows
# or: source .venv/bin/activate  # Linux/Mac

# Start server
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Then Open:

**Dashboard:** http://localhost:8000  
**API Docs:** http://localhost:8000/docs

---

## 📊 Dashboard Features

### 1. Join Meeting Section

- **Meeting ID**: Your internal identifier (e.g., "demo-1")
- **Meeting URL**: Full Teams or Google Meet URL
- **Platform**: Select "Google Meet" or "Microsoft Teams"
- Click **"Start Bot Session"** to begin

The form validates inputs and shows success/error messages.

### 2. Active Sessions Section

Shows all bot sessions with:
- **Status badges**: Color-coded by state
  - 🟡 **Creating/Joining** - Bot is starting
  - 🟢 **In Meeting** - Bot is active
  - ⚪ **Ended** - Session completed
  - 🔴 **Failed** - Error occurred
- **Session details**: Meeting ID, Platform, Session ID
- **Timestamps**: When session started/ended
- **Auto-refresh**: Updates every 5 seconds

### 3. Live Logs Section

Real-time log viewer with:
- **Color-coded levels**: INFO (green), WARNING (yellow), ERROR (red)
- **Filtering**: Filter by log level (INFO, WARNING, ERROR)
- **Search**: Search by text, meeting ID, or session ID
- **Auto-scroll**: Automatically scrolls to latest logs
- **Clear button**: Clear all logs from buffer

Logs include:
- Timestamp
- Log level
- Message
- Meeting/Session IDs (if applicable)
- Event type (if applicable)

---

## 🔧 Configuration

### Environment Variables

Set these in your terminal before starting:

```bash
# Browser mode
export HEADLESS=true          # false to see browser window

# Concurrency
export MAX_CONCURRENT_SESSIONS=10

# Azure (optional)
export AZURE_BLOB_CONNECTION_STRING="..."
export AZURE_BLOB_CONTAINER="meeting-audio"
export AZURE_EVENTGRID_ENDPOINT="https://..."
export AZURE_EVENTGRID_KEY="..."

# Diarisation (optional)
export DIARIZATION_API_URL="https://your-service/api/analyze"
```

---

## 📱 API Endpoints

All endpoints are available via the dashboard or directly:

- `GET /` - Dashboard UI
- `POST /join-meeting` - Start bot session
- `GET /sessions` - List all sessions (JSON)
- `GET /logs` - Get logs with filters (JSON)
- `POST /logs/clear` - Clear log buffer
- `GET /healthz` - Health check
- `GET /docs` - Interactive API documentation

---

## 🎨 Dashboard UI

The dashboard is:
- ✅ **Responsive** - Works on all screen sizes
- ✅ **Real-time** - Auto-refreshes every 2-5 seconds
- ✅ **Modern** - Clean, professional design
- ✅ **Dark logs** - Easy-to-read terminal-style log viewer
- ✅ **Color-coded** - Visual status indicators

---

## 🐛 Troubleshooting

### Dashboard not loading?

1. Check that `static/` folder exists with `index.html`
2. Check terminal for errors
3. Try accessing: http://localhost:8000/docs (API should work)

### Logs not showing?

- Logs buffer stores last 2000 entries
- Clear and wait for new logs if needed
- Check browser console for errors

### Sessions not updating?

- Check that server is running
- Check browser console for API errors
- Refresh the page manually

---

## 📝 Next Steps

The dashboard provides full visibility into your meeting bot. You can:
1. Start multiple bot sessions easily
2. Monitor all sessions in one place
3. Debug issues with live logs
4. Track meeting lifecycle from start to finish

Enjoy! 🎉






