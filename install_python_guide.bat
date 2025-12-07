@echo off
REM ============================================================
REM Python Installation Guide
REM ============================================================
echo.
echo ============================================================
echo         Python Installation Guide
echo ============================================================
echo.
echo The Meeting Bot requires Python 3.11 or newer.
echo.
echo ============================================================
echo         Quick Installation Steps
echo ============================================================
echo.
echo Method 1: Microsoft Store (Easiest)
echo ------------------------------------
echo 1. Press Windows key, type "Microsoft Store"
echo 2. Search for "Python 3.11" or "Python 3.12"
echo 3. Click "Get" or "Install"
echo 4. IMPORTANT: After installation, Python should be in PATH automatically
echo.
echo Method 2: Python.org (Recommended)
echo ------------------------------------
echo 1. Open your browser
echo 2. Go to: https://www.python.org/downloads/
echo 3. Click the big yellow "Download Python" button
echo 4. Run the downloaded installer (.exe file)
echo 5. IMPORTANT: On the first screen, CHECK THIS BOX:
echo    [x] Add Python to PATH
echo 6. Click "Install Now"
echo 7. Wait for installation to complete
echo.
echo ============================================================
echo         After Installation
echo ============================================================
echo.
echo IMPORTANT: Restart your computer after installing Python!
echo.
echo Then:
echo   1. Run check_python.bat to verify installation
echo   2. Run start.bat to start the Meeting Bot
echo.
echo ============================================================
echo.
echo Would you like to:
echo   1. Open Python download page in browser
echo   2. Open Microsoft Store
echo   3. Just show this guide
echo.
choice /C 123 /M "Choose an option"
if errorlevel 3 goto :end
if errorlevel 2 goto :store
if errorlevel 1 goto :download

:download
echo.
echo Opening Python download page...
start https://www.python.org/downloads/
goto :end

:store
echo.
echo Opening Microsoft Store...
start ms-windows-store://pdp/?ProductId=9NRWMJP3717K
goto :end

:end
echo.
echo After installing Python, restart your computer and run check_python.bat
echo.
pause



