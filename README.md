## Meeting Bot (Playwright + FastAPI)

Python 3.11+ service that runs Playwright-powered bots to join Teams and Google Meet meetings, track sessions, capture audio, identify speakers, and save everything locally to JSON files.

**✨ Features:**
- 🖥️ **Visible Browser** - See the bot joining meetings (non-headless by default)
- 💾 **Local Storage** - All data saved to JSON files on your machine (no Azure required!)
- 📊 **Web Dashboard** - Beautiful UI to manage everything

### 🚀 Quick Start (Easiest Way)

**Windows:**
```cmd
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

The script will automatically:
- Create virtual environment if needed
- Install all dependencies
- Install Playwright Chromium
- Start the server

**Then open your browser to:** `http://localhost:8000` 🎉

You'll see a beautiful **dashboard UI** where you can:
- ✅ Join meetings with a simple form
- ✅ View all active sessions in real-time
- ✅ See live logs with filtering and search
- ✅ Monitor bot status

---

### 📋 Manual Installation

1. **Install Python 3.11+**
   - Download from [python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH" during installation

2. **Create venv and install**

```bash
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# or: source .venv/bin/activate  # Linux/Mac

pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install chromium
```

3. **Run the server**

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

4. **Open Dashboard**

Open your browser to: **http://localhost:8000**

You'll see the dashboard UI automatically!

---

### 📊 Using the Dashboard

1. **Join a Meeting:**
   - Enter Meeting ID (e.g., "demo-1")
   - Paste the meeting URL (Google Meet or Teams)
   - Select platform
   - Click "Start Bot Session"

2. **Monitor Sessions:**
   - See all active sessions with status badges
   - Sessions auto-refresh every 5 seconds
   - Color-coded by status (creating, joining, in meeting, ended, failed)

3. **View Live Logs:**
   - See all system logs in real-time
   - Filter by log level (INFO, WARNING, ERROR)
   - Search logs by text, meeting ID, or session ID
   - Auto-scrolls to latest logs

---

### 🔧 API Endpoints

- `GET /` - Dashboard UI
- `POST /join-meeting` - Start a bot session
- `GET /sessions` - List all sessions
- `GET /logs` - Get logs (with optional filters)
- `GET /healthz` - Health check
- `GET /docs` - API documentation (Swagger)

### 📁 Local Storage (Default)

**All data is saved locally** in the `data/` folder:
- ✅ **Events** → `data/events/YYYYMMDD.jsonl` (JSON Lines format)
- ✅ **Audio files** → `data/audio/meeting_id/session_id/*.wav`
- ✅ **Session data** → `data/sessions/session_id.json` (complete summary)

No Azure needed! Just open the JSON files to see all your meeting data.

See `LOCAL_STORAGE.md` for details.

### ☁️ Azure Configuration (Optional)

If you want to also sync to Azure, set these environment variables:

- `AZURE_BLOB_CONNECTION_STRING`
- `AZURE_BLOB_CONTAINER`
- `AZURE_EVENTGRID_ENDPOINT`
- `AZURE_EVENTGRID_KEY`
- `DIARIZATION_API_URL` (optional HTTP service to analyse audio chunks)

When set, data will be saved **both locally AND to Azure** (backup/cloud sync).

### High-level architecture

- `FastAPI` exposes `/join-meeting` and future admin endpoints.
- `SessionManager` coordinates concurrent Playwright sessions with a configurable limit.
- Platform-specific join flows for Teams and Google Meet live under `meeting_flow/`.
- Audio capture & participant polling loops run every 30s while the meeting is active.
- Azure Blob Storage + Event Grid integrations handle audio chunk blobs and events (`bot_joined`, `audio_chunk_created`, `participant_update`, `meeting_summary`).


