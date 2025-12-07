@echo off
REM Kill any process using port 8000
echo.
echo ============================================================
echo Killing process using port 8000...
echo ============================================================
echo.

REM Find process using port 8000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    set PID=%%a
    echo Found process ID: %%a
    echo Killing process...
    taskkill /F /PID %%a
    if errorlevel 1 (
        echo ERROR: Could not kill process %%a
        echo You may need to run this script as Administrator
    ) else (
        echo ✅ Successfully killed process %%a
    )
)

echo.
echo Done! You can now start the bot with start.bat
echo.
pause

