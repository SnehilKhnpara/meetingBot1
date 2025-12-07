@echo off
REM ============================================================
REM Meeting Bot - Simple Startup (Non-Headless by Default)
REM ============================================================
echo.
echo ============================================================
echo         Meeting Bot Starting...
echo ============================================================
echo.

REM Set the Python executable path
set VENV_PYTHON=.venv\Scripts\python.exe

REM Check if venv exists
if exist "%VENV_PYTHON%" (
    echo Using existing virtual environment...
    goto :check_deps
)

REM Create venv if it doesn't exist
echo Creating virtual environment...
REM Try different Python commands
python --version >nul 2>&1
if not errorlevel 1 (
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment with python
        pause
        exit /b 1
    )
    goto :check_deps
)

py --version >nul 2>&1
if not errorlevel 1 (
    py -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment with py
        pause
        exit /b 1
    )
    goto :check_deps
)

echo ERROR: Python not found. Please install Python 3.11+ and add it to PATH
pause
exit /b 1

:check_deps
REM Verify venv Python exists
if not exist "%VENV_PYTHON%" (
    echo ERROR: Virtual environment Python not found at %VENV_PYTHON%
    pause
    exit /b 1
)

REM Install dependencies if needed
echo Checking dependencies...
"%VENV_PYTHON%" -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    echo This may take a few minutes...
    "%VENV_PYTHON%" -m pip install --upgrade pip
    if errorlevel 1 (
        echo ERROR: Failed to upgrade pip
        pause
        exit /b 1
    )
    "%VENV_PYTHON%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies from requirements.txt
        pause
        exit /b 1
    )
    echo Installing Playwright Chromium...
    "%VENV_PYTHON%" -m playwright install chromium
    if errorlevel 1 (
        echo WARNING: Failed to install Playwright Chromium
    )
    echo Dependencies installed successfully!
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
"%VENV_PYTHON%" -c "import sys; sys.path.insert(0, '.'); from src.main import app; print('✅ All imports successful!')" 2>&1
if errorlevel 1 (
    echo.
    echo ============================================================
    echo ERROR: Failed to import modules!
    echo ============================================================
    echo.
    echo Please check the error message above.
    echo.
    echo Trying to reinstall dependencies...
    "%VENV_PYTHON%" -m pip install --upgrade pip
    "%VENV_PYTHON%" -m pip install -r requirements.txt
    echo.
    echo Please run start.bat again after dependencies are installed.
    echo.
    pause
    exit /b 1
)

echo ✅ Imports successful!
echo.

REM Start the server
echo Starting server...
"%VENV_PYTHON%" -m uvicorn src.main:app --host 0.0.0.0 --port 8000

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
