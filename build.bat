@echo off
REM Pyrox Build Script (Windows Batch)
REM Simple build script for maximum Windows compatibility

setlocal EnableDelayedExpansion

echo === Pyrox Build Script ===
echo Starting build process...

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo ✓ Python detected

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment exists
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

echo ✓ Virtual environment activated

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip --quiet

REM Install requirements
if exist "requirements.txt" (
    echo Installing requirements...
    python -m pip install -r requirements.txt --upgrade --quiet
    if errorlevel 1 (
        echo Error: Failed to install requirements
        pause
        exit /b 1
    )
    echo ✓ Requirements installed
) else (
    echo Warning: requirements.txt not found
)

REM Install package in development mode
if exist "pyproject.toml" (
    echo Installing Pyrox package...
    python -m pip install -e . --upgrade --quiet
    if errorlevel 1 (
        echo Error: Failed to install Pyrox package
        pause
        exit /b 1
    )
    echo ✓ Pyrox package installed
) else (
    echo Warning: pyproject.toml not found
)

REM Verify installation
echo Verifying installation...
python -c "import pyrox; print('✓ Pyrox module imported successfully')" 2>nul
if errorlevel 1 (
    echo Warning: Could not import pyrox module
) else (
    echo ✓ Build completed successfully!
)

echo.
echo Build process completed!
echo You can now run: deploy.bat or deploy.ps1
pause
