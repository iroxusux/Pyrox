#!/bin/bash

# Global variable to store the log file path
LOG_FILE=""


# Function to activate a virtual environment
activate_venv() {
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows/Git Bash
        source .venv/Scripts/activate
    else
        # Linux/Mac
        source .venv/bin/activate
    fi
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        log_and_echo "Error: Failed to activate virtual environment"
        return 1
    fi
    log_and_echo "✓ Virtual environment activated: $VIRTUAL_ENV"
    return 0
}


# Function to check if a virtual environment exists and create one if not
check_and_create_venv() {
    if [ ! -d ".venv" ]; then
        log_and_echo "Creating virtual environment..."
        python -m venv .venv 2>&1 | while IFS= read -r line; do
            log_and_echo "$line"
        done
        log_and_echo "✓ Virtual environment created"
    else
        log_and_echo "✓ Virtual environment exists"
    fi
}


# Function to check if Python is installed
check_python_installed() {
    if ! command -v python &> /dev/null; then
        log_and_echo "Error: Python is not installed or not in PATH"
        return 1
    fi

    log_and_echo "✓ Python detected"
    return 0
}


# Function to check if the required Python version is installed
# Parameter 1: Required major version (e.g., 3)
# Parameter 2: Required minor version (e.g., 13)
check_python_version_installed() {
    local required_version_major="$1"
    local required_version_minor="$2"
    local python_version

    python_version=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
    if [ -z "$python_version" ]; then
        log_and_echo "Error: Unable to determine Python version"
        return 1
    fi

    if ! python -c "import sys; exit(0 if sys.version_info >= ($required_version_major, $required_version_minor) else 1)" 2>/dev/null; then
        log_and_echo "Error: Python $required_version_major , $required_version_minor or higher is required. Found: $python_version"
        return 2
    fi

    log_and_echo "✓ Python $python_version detected"
    return 0
}


# Function to print installed packages from a python environment
get_installed_packages() {
    python -m pip list --format=columns 2>&1 | while IFS= read -r line; do
        log_and_echo "$line"
    done
}


# Function to get the current log file path (utility function)
get_log_file() {
    echo "$LOG_FILE"
}


# Function to install local dependencies from requirements.txt or pyproject.toml
install_local_dependencies() {
    if [ -f "requirements.txt" ]; then
        log_and_echo "Installing requirements from requirements.txt..."
        python -m pip install -r requirements.txt --upgrade 2>&1 | while IFS= read -r line; do
            log_and_echo "$line"
        done
        log_and_echo "✓ Requirements installed from requirements.txt"
    else
        log_and_echo "Warning: requirements.txt not found"
    fi

    if [ -f "pyproject.toml" ]; then
        python -m pip install -e . --upgrade 2>&1 | while IFS= read -r line; do
            log_and_echo "$line"
        done
        log_and_echo "✓ package installed from pyproject.toml"
    else
        log_and_echo "Warning: pyproject.toml not found, skipping package installation"
    fi
}


# Function to log and display messages
# Parameter 1: Message string to log and echo
log_and_echo() {
    local message="$1"
    
    # Check if logging has been setup
    if [ -z "$LOG_FILE" ]; then
        echo "WARNING: Logging not setup. Call setup_logging first."
        echo "$message"
        return 1
    fi
    
    # Log and echo the message
    echo "$message" | tee -a "$LOG_FILE"
    
    return 0
}


# Function to safety activate virtual environment
safe_activate_venv() {
    activate_venv
    if [ $? -ne 0 ]; then
        exit 1
    fi
    return 0
}


# Function to safety exit if python is not detected
safe_check_python_installed() {
    check_python_installed
    if [ $? -ne 0 ]; then
        exit 1
    fi
    return 0
}

# Function to safely exit if python version is not sufficient
safe_check_python_version_installed() {
    local required_version_major="$1"
    local required_version_minor="$2"
    check_python_version_installed "$required_version_major" "$required_version_minor"
    if [ $? -ne 0 ]; then
        exit 1
    fi
    return 0
}


# Function to setup logging
# Parameter 1: Directory path for logs
# Parameter 2: Appended name for the log file (without extension)
setup_logging() {
    local log_dir="$1"
    local log_name="$2"
    
    # Validate parameters
    if [ -z "$log_dir" ] || [ -z "$log_name" ]; then
        echo "ERROR: setup_logging requires 2 parameters: <log_directory> <log_name>"
        echo "Usage: setup_logging 'logs' 'deploy'"
        return 1
    fi
    
    # Create logs directory if it doesn't exist
    mkdir -p "$log_dir"
    
    # Set log file with timestamp
    LOG_FILE="${log_dir}/${log_name}_$(date +%Y%m%d_%H%M%S).log"
    
    # Initialize log file with header
    echo "=== Log started at $(date) ===" > "$LOG_FILE"
    
    return 0
}


# Function to upgrade pip
upgrade_pip() {
    log_and_echo "Upgrading pip..."
    python -m pip install --upgrade pip 2>&1 | while IFS= read -r line; do
        log_and_echo "$line"
    done
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        log_and_echo "Error: Failed to upgrade pip"
        return 1
    fi
    log_and_echo "✓ pip upgraded successfully"
    return 0
}