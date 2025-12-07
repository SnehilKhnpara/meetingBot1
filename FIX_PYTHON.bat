@echo off
REM ============================================================
REM Quick Python Fix Script
REM ============================================================
echo.
echo ============================================================
echo         Python Fix Helper
echo ============================================================
echo.

REM Check if check_python.bat exists and run it
if exist check_python.bat (
    echo Running Python diagnostic...
    echo.
    call check_python.bat
    if errorlevel 1 (
        echo.
        echo Diagnostic completed. See PYTHON_NOT_FOUND.md for help.
    )
) else (
    echo check_python.bat not found.
    echo.
    echo Please install Python 3.11+ from python.org
    echo Make sure to check "Add Python to PATH" during installation!
)

echo.
pause



