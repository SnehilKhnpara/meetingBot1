@echo off
REM ============================================================
REM First-Time Setup Wizard
REM ============================================================
echo.
echo ============================================================
echo         Meeting Bot - First-Time Setup
echo ============================================================
echo.
echo This will help you set up the bot for the first time.
echo.

REM Check if already set up
if exist "profiles\google_main\Default\Cookies" (
    echo [INFO] Profile already exists and appears to be logged in.
    echo.
    choice /C YN /M "Do you want to reset and login again"
    if errorlevel 2 (
        echo Setup cancelled.
        pause
        exit /b 0
    )
    echo.
    echo Removing existing profile...
    if exist "profiles\google_main" (
        rmdir /s /q "profiles\google_main"
        echo Profile removed.
    )
)

echo.
echo ============================================================
echo         Setup Instructions
echo ============================================================
echo.
echo Step 1: The bot will start with browser visible
echo Step 2: Open dashboard at http://localhost:8000
echo Step 3: Join a test meeting
echo Step 4: When browser opens, sign in to Google
echo Step 5: Complete 2FA/CAPTCHA if needed
echo Step 6: Close browser - login is saved!
echo.
echo After setup, you can run 'start.bat' normally.
echo Browser can be hidden (HEADLESS=true) after first login.
echo.
echo ============================================================
echo.
pause

REM Set up for first-time login
set HEADLESS=false
set GOOGLE_LOGIN_REQUIRED=true
set PROFILES_ROOT=profiles
set GMEET_PROFILE_NAME=google_main

REM Run the main startup script
call start.bat



