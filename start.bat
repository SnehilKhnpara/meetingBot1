@echo off
REM ============================================================
REM Meeting Bot - Simple Startup (Non-Headless by Default)
REM ============================================================
echo.
echo ============================================================
echo         Meeting Bot Starting...
echo ============================================================
echo.

REM If venv exists, use it directly (bypasses PATH issues)
if exist ".venv\Scripts\python.exe" (
    echo Using existing virtual environment...
    call .venv\Scripts\activate.bat
    goto :start_server
)

REM Create venv if it doesn't exist
echo Creating virtual environment...
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python not found. Please install Python 3.11+
        pause
        exit /b 1
    )
    py -m venv .venv
) else (
    python -m venv .venv
)

if errorlevel 1 (
    echo ERROR: Failed to create virtual environment.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

REM Install dependencies if needed
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    python -m playwright install chromium
)

:start_server
REM Set defaults - Non-headless (visible browser)
if not defined HEADLESS set HEADLESS=false
if not defined PROFILES_ROOT set PROFILES_ROOT=profiles
if not defined GMEET_PROFILE_NAME set GMEET_PROFILE_NAME=google_main
if not defined GOOGLE_LOGIN_REQUIRED set GOOGLE_LOGIN_REQUIRED=true
if not defined MAX_CONCURRENT_MEETINGS set MAX_CONCURRENT_MEETINGS=5
if not defined MAX_CONCURRENT_SESSIONS set MAX_CONCURRENT_SESSIONS=10
if not defined DATA_DIR set DATA_DIR=data

echo.
echo ============================================================
echo Meeting Bot Starting...
echo ============================================================
echo Dashboard: http://localhost:8000
echo Browser:   Visible (HEADLESS=false)
echo.
echo Press Ctrl+C to stop
echo ============================================================
echo.

REM Test imports before starting server
echo Testing imports...
python -c "import sys; sys.path.insert(0, '.'); from src.main import app; print('Imports OK')" 2>&1
if errorlevel 1 (
    echo.
    echo ============================================================
    echo ERROR: Failed to import modules!
    echo ============================================================
    echo.
    echo Please check the error message above.
    echo.
    pause
    exit /b 1
)

echo Imports successful!
echo.

REM Start the server
echo Starting server...
uvicorn src.main:app --host 0.0.0.0 --port 8000

REM If server exits, pause so user can see any errors
if errorlevel 1 (
    echo.
    echo ============================================================
    echo ERROR: Server stopped unexpectedly!
    echo ============================================================
    echo.
    echo Please check the error messages above.
    echo.
    pause
    exit /b 1
)
