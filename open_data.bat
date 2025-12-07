@echo off
REM ============================================================
REM Quick Data Viewer - Opens data folders
REM ============================================================
echo.
echo ============================================================
echo         Meeting Bot Data Viewer
echo ============================================================
echo.

echo Opening data folders...
echo.

REM Open main data folder
if exist "data" (
    explorer data
    timeout /t 1 >nul
) else (
    echo Data folder not found!
    pause
    exit /b 1
)

REM Ask what to open
echo.
echo What would you like to view?
echo.
echo 1. Audio files
echo 2. Session data
echo 3. Events
echo 4. All folders
echo 5. Run Python viewer script
echo.
choice /C 12345 /M "Choose option"

if errorlevel 5 goto :python_viewer
if errorlevel 4 goto :all
if errorlevel 3 goto :events
if errorlevel 2 goto :sessions
if errorlevel 1 goto :audio

:audio
explorer data\audio
goto :end

:sessions
explorer data\sessions
goto :end

:events
explorer data\events
goto :end

:all
explorer data\audio
timeout /t 1 >nul
explorer data\sessions
timeout /t 1 >nul
explorer data\events
goto :end

:python_viewer
echo.
echo Running Python data viewer...
python view_data.py
goto :end

:end
echo.
pause



