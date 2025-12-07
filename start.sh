#!/bin/bash
# ============================================================
# One-Click Meeting Bot Startup Script (Linux/Mac)
# ============================================================

echo ""
echo "============================================================"
echo "        Meeting Bot - One-Click Startup"
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed or not in PATH"
    echo "Please install Python 3.11+ and try again"
    exit 1
fi

# Check if venv exists, create if not
if [ ! -d ".venv" ]; then
    echo "[SETUP] Creating virtual environment..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment"
        exit 1
    fi
fi

# Activate venv
source .venv/bin/activate

# Check if dependencies are installed
python -c "import fastapi" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[SETUP] Installing dependencies..."
    echo "This may take a few minutes..."
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to install dependencies"
        exit 1
    fi
    echo "[SETUP] Installing Playwright Chromium..."
    python -m playwright install chromium
fi

# ============================================================
# Configuration - Set defaults
# ============================================================
export HEADLESS=${HEADLESS:-false}
export PROFILES_ROOT=${PROFILES_ROOT:-profiles}
export GMEET_PROFILE_NAME=${GMEET_PROFILE_NAME:-google_main}
export GOOGLE_LOGIN_REQUIRED=${GOOGLE_LOGIN_REQUIRED:-true}
export MAX_CONCURRENT_MEETINGS=${MAX_CONCURRENT_MEETINGS:-5}
export MAX_CONCURRENT_SESSIONS=${MAX_CONCURRENT_SESSIONS:-10}
export DATA_DIR=${DATA_DIR:-data}

# ============================================================
# First-Time Setup Check
# ============================================================
PROFILE_DIR="$PROFILES_ROOT/$GMEET_PROFILE_NAME"
FIRST_TIME=false

if [ ! -d "$PROFILE_DIR" ]; then
    FIRST_TIME=true
    echo ""
    echo "============================================================"
    echo "        FIRST-TIME SETUP DETECTED"
    echo "============================================================"
    echo ""
    echo "This appears to be your first time running the bot."
    echo "You will need to log in to Google once."
    echo ""
    echo "Instructions:"
    echo "  1. The browser will open when you join a meeting"
    echo "  2. Sign in to Google with your account"
    echo "  3. Complete 2FA/CAPTCHA if needed"
    echo "  4. After login, the browser will be saved for future use"
    echo ""
    read -p "Press Enter to continue..."
    echo ""
elif [ ! -f "$PROFILE_DIR/Default/Cookies" ] && [ ! -f "$PROFILE_DIR/Local State" ]; then
    FIRST_TIME=true
    echo ""
    echo "============================================================"
    echo "        PROFILE NOT LOGGED IN"
    echo "============================================================"
    echo ""
    echo "Profile exists but doesn't appear to be logged in."
    echo "You may need to log in again."
    echo ""
    read -p "Press Enter to continue..."
    echo ""
fi

# ============================================================
# Display Configuration
# ============================================================
echo "============================================================"
echo "        Configuration"
echo "============================================================"
echo ""
echo "Browser Mode:        $HEADLESS (set HEADLESS=true/false to change)"
echo "Profiles Directory:  $PROFILES_ROOT"
echo "Default Profile:     $GMEET_PROFILE_NAME"
echo "Login Required:      $GOOGLE_LOGIN_REQUIRED"
echo "Max Concurrent:      $MAX_CONCURRENT_MEETINGS meetings"
echo ""

if [ "$FIRST_TIME" = true ]; then
    echo "[INFO] Browser will be VISIBLE for first-time login"
    export HEADLESS=false
    echo "Browser Mode:        $HEADLESS (forced for first login)"
    echo ""
fi

# ============================================================
# Start the Server
# ============================================================
echo "============================================================"
echo "        Starting Meeting Bot Server"
echo "============================================================"
echo ""
echo "Dashboard will be available at:"
echo "   http://localhost:8000"
echo ""
echo "API Documentation:"
echo "   http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo "============================================================"
echo ""

# Start the server
uvicorn src.main:app --host 0.0.0.0 --port 8000

# If we get here, server stopped
echo ""
echo "Server stopped."
