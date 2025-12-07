@echo off
REM Quick credential setup script
echo ========================================
echo Setting up Automatic Login Credentials
echo ========================================
echo.
echo Email: amitunadkat.work@gmail.com
echo.

REM Check if password is set
if not defined GMEET_PASSWORD (
    echo Please enter your password for amitunadkat.work@gmail.com:
    set /p GMEET_PASSWORD=Password: 
)

if "%GMEET_PASSWORD%"=="" (
    echo ERROR: Password cannot be empty!
    pause
    exit /b 1
)

echo.
echo Saving credentials...
set /p GMEET_PASSWORD=Password: 
python scripts/save_credentials.py --platform gmeet --email amitunadkat.work@gmail.com --password %GMEET_PASSWORD%
echo.

if errorlevel 1 (
    echo ERROR: Failed to save credentials!
    pause
    exit /b 1
)

echo ========================================
echo Credentials saved successfully!
echo Bot will now automatically login with amitunadkat.work@gmail.com
echo ========================================
echo.
pause

