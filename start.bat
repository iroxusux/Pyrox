@echo off
REM Pyrox Launcher
REM This script activates the virtual environment and starts the application

echo ======================================
echo      Pyrox Application Launcher
echo ======================================
echo.

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo.
    echo Please run install.sh first to set up the environment.
    echo.
    pause
    exit /b 1
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment.
    echo.
    pause
    exit /b 1
)

echo Virtual environment activated successfully.
echo.
echo Starting Pyrox application...
echo.
echo ======================================
echo.

REM Run the application as a module
python -m pyrox

REM Capture the exit code
set EXIT_CODE=%errorlevel%

echo.
echo ======================================
echo Application exited with code: %EXIT_CODE%
echo ======================================
echo.

REM Deactivate virtual environment
call deactivate 2>nul

pause
exit /b %EXIT_CODE%
