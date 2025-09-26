#!/bin/bash

# Pyrox Build Script
# This script sets up the development environment and installs dependencies

# Create logs directory if it doesn't exist
mkdir -p logs

# Set log file with timestamp
LOG_FILE="logs/build_$(date +%Y%m%d_%H%M%S).log"

# Function to log and display messages
log_and_echo() {
    echo "$1" | tee -a "$LOG_FILE"
}

# Redirect all output to log file and console
exec > >(tee -a "$LOG_FILE") 2>&1

set -e  # Exit on any error

# Change to script directory
cd "$(dirname "$0")"

log_and_echo "=== Pyrox Build Script ==="
log_and_echo "Starting build process..."

# Check if Python is available
if ! command -v python &> /dev/null; then
    log_and_echo "Error: Python is not installed or not in PATH"
    exit 1
fi

# Check Python version (requires 3.13+)
python_version=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.13"

if ! python -c "import sys; exit(0 if sys.version_info >= (3, 13) else 1)" 2>/dev/null; then
    log_and_echo "Error: Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

log_and_echo "✓ Python $python_version detected"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    log_and_echo "Creating virtual environment..."
    python -m venv .venv
    log_and_echo "✓ Virtual environment created"
else
    log_and_echo "✓ Virtual environment exists"
fi

# Activate virtual environment
log_and_echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows/Git Bash
    source .venv/Scripts/activate
else
    # Linux/Mac
    source .venv/bin/activate
fi

if [[ "$VIRTUAL_ENV" == "" ]]; then
    log_and_echo "Error: Failed to activate virtual environment"
    exit 1
fi

log_and_echo "✓ Virtual environment activated: $VIRTUAL_ENV"

# Upgrade pip first
log_and_echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install/upgrade requirements
if [ -f "requirements.txt" ]; then
    log_and_echo "Installing requirements from requirements.txt..."
    python -m pip install -r requirements.txt --upgrade
    log_and_echo "✓ Requirements installed"
else
    log_and_echo "Warning: requirements.txt not found"
fi

# Install the package in development mode
log_and_echo "Installing Pyrox package in development mode..."
if [ -f "pyproject.toml" ]; then
    python -m pip install -e . --upgrade
    log_and_echo "✓ Pyrox package installed in development mode"
else
    log_and_echo "Warning: pyproject.toml not found, skipping package installation"
fi

# Verify installation
log_and_echo "Verifying installation..."
if python -c "import pyrox; print(f'✓ Pyrox module imported successfully')" 2>/dev/null; then
    log_and_echo "✓ Build completed successfully!"
else
    log_and_echo "Warning: Could not import pyrox module"
fi

log_and_echo "=== Build Summary ==="
log_and_echo "Python version: $python_version"
log_and_echo "Virtual environment: $VIRTUAL_ENV"
log_and_echo "Installed packages:"
python -m pip list --format=columns | head -20

log_and_echo ""
log_and_echo "Build process completed!"
log_and_echo "You can now run the deployment script."
