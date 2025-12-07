@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM Python Installation Checker & Path Helper
REM ============================================================
echo.
echo ============================================================
echo         Checking Python Installation
echo ============================================================
echo.

REM Try different Python commands
echo Checking for Python...
echo.

REM Try 'python'
where python >nul 2>&1
if %errorlevel% == 0 (
    echo [FOUND] Python found as 'python'
    python --version
    echo.
    echo Python is installed and accessible!
    echo.
    pause
    exit /b 0
)

REM Try 'python3'
where python3 >nul 2>&1
if %errorlevel% == 0 (
    echo [FOUND] Python found as 'python3'
    python3 --version
    echo.
    echo Python is installed but you need to use 'python3' command.
    echo.
    echo Would you like to create a 'python.bat' wrapper? (Y/N)
    choice /C YN /M "Create wrapper"
    if errorlevel 2 (
        echo Skipped wrapper creation.
        pause
        exit /b 0
    )
    echo.
    echo Creating python.bat wrapper...
    echo @python3 %%* > python.bat
    echo Wrapper created! Try running start.bat again.
    echo.
    pause
    exit /b 0
)

REM Try 'py' launcher
where py >nul 2>&1
if %errorlevel% == 0 (
    echo [FOUND] Python found via 'py' launcher
    py --version
    echo.
    echo Python is installed but you need to use 'py' command.
    echo.
    echo Creating python.bat wrapper...
    echo @py %%* > python.bat
    echo Wrapper created! Try running start.bat again.
    echo.
    pause
    exit /b 0
)

REM Check common installation paths
echo [NOT FOUND] Python not found in PATH.
echo.
echo Checking common installation locations...
echo.

set FOUND=0

REM Check C:\Python* folders
if exist "C:\Python*" (
    for /d %%d in (C:\Python* 2^>nul) do (
        if exist "%%d\python.exe" (
            echo [FOUND] Python at: %%d\python.exe
            "%%d\python.exe" --version 2>nul
            if !errorlevel! == 0 (
                echo.
                echo Creating python.bat wrapper...
                echo @"%%d\python.exe" %%* > python.bat
                echo.
                echo Wrapper created! Try running start.bat again.
                set FOUND=1
                goto :found
            )
        )
    )
)

REM Check Program Files
for /d %%d in ("C:\Program Files\Python*" 2^>nul) do (
    if exist "%%d\python.exe" (
        echo [FOUND] Python at: %%d\python.exe
        "%%d\python.exe" --version 2>nul
        if !errorlevel! == 0 (
            echo.
            echo Creating python.bat wrapper...
            echo @"%%d\python.exe" %%* > python.bat
            echo.
            echo Wrapper created! Try running start.bat again.
            set FOUND=1
            goto :found
        )
    )
)

REM Check user AppData
if exist "%LOCALAPPDATA%\Programs\Python" (
    for /d %%d in ("%LOCALAPPDATA%\Programs\Python\Python*" 2^>nul) do (
        if exist "%%d\python.exe" (
            echo [FOUND] Python at: %%d\python.exe
            "%%d\python.exe" --version 2>nul
            if !errorlevel! == 0 (
                echo.
                echo Creating python.bat wrapper...
                echo @"%%d\python.exe" %%* > python.bat
                echo.
                echo Wrapper created! Try running start.bat again.
                set FOUND=1
                goto :found
            )
        )
    )
)

:found
if %FOUND% == 0 (
    echo.
    echo ============================================================
    echo         Python Not Found
    echo ============================================================
    echo.
    echo Python 3.11+ is required but not found on your system.
    echo.
    echo ============================================================
    echo         Installation Options
    echo ============================================================
    echo.
    echo Option 1: Install from Microsoft Store (Easiest)
    echo   1. Open Microsoft Store
    echo   2. Search for "Python 3.11" or "Python 3.12"
    echo   3. Click Install
    echo   4. IMPORTANT: During installation, check "Add Python to PATH"
    echo   5. Restart your computer after installation
    echo.
    echo Option 2: Install from python.org (Recommended)
    echo   1. Go to: https://www.python.org/downloads/
    echo   2. Download Python 3.11 or 3.12
    echo   3. Run the installer
    echo   4. IMPORTANT: Check "Add Python to PATH" at the bottom!
    echo   5. Click "Install Now"
    echo   6. Restart your computer after installation
    echo.
    echo Option 3: If Python is already installed
    echo   Python might be installed but not in PATH.
    echo   Please add Python to your system PATH manually.
    echo.
    echo ============================================================
    echo.
    echo After installing Python:
    echo   1. Restart your computer (important!)
    echo   2. Run this script again to verify
    echo   3. Then run start.bat
    echo.
    pause
    exit /b 1
) else (
    pause
    exit /b 0
)

