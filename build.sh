#!/bin/bash

# Pyrox Build Script
# This script sets up the development environment and installs dependencies

set -e  # Exit on any error

# Change to script directory
cd "$(dirname "$0")"

echo "=== Pyrox Build Script ==="
echo "Starting build process..."

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

# Check Python version (requires 3.13+)
python_version=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.13"

if ! python -c "import sys; exit(0 if sys.version_info >= (3, 13) else 1)" 2>/dev/null; then
    echo "Error: Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

echo "✓ Python $python_version detected"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows/Git Bash
    source .venv/Scripts/activate
else
    # Linux/Mac
    source .venv/bin/activate
fi

if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Error: Failed to activate virtual environment"
    exit 1
fi

echo "✓ Virtual environment activated: $VIRTUAL_ENV"

# Upgrade pip first
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install/upgrade requirements
if [ -f "requirements.txt" ]; then
    echo "Installing requirements from requirements.txt..."
    python -m pip install -r requirements.txt --upgrade
    echo "✓ Requirements installed"
else
    echo "Warning: requirements.txt not found"
fi

# Install the package in development mode
echo "Installing Pyrox package in development mode..."
if [ -f "pyproject.toml" ]; then
    python -m pip install -e . --upgrade
    echo "✓ Pyrox package installed in development mode"
else
    echo "Warning: pyproject.toml not found, skipping package installation"
fi

# Verify installation
echo "Verifying installation..."
if python -c "import pyrox; print(f'✓ Pyrox module imported successfully')" 2>/dev/null; then
    echo "✓ Build completed successfully!"
else
    echo "Warning: Could not import pyrox module"
fi

echo "=== Build Summary ==="
echo "Python version: $python_version"
echo "Virtual environment: $VIRTUAL_ENV"
echo "Installed packages:"
python -m pip list --format=columns | head -20

echo ""
echo "Build process completed!"
echo "You can now run the deployment script."
