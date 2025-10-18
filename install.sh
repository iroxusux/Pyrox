#!/bin/bash
# Install script for setting up the development environment and installing dependencies

# Configuration
PACKAGE_NAME="Pyrox"
PACKAGE_NAME_LOWER="pyrox"

# Change to script directory
cd "$(dirname "$0")"

# Source utilities
source ./utils/utils.sh

# Setup logging
setup_logging "logs" "install"

# Enable strict error handling
set -e  # Exit on any error
set -u  # Exit on undefined variables
set -o pipefail  # Exit on pipe failures

# Error handling function
handle_error() {
    local exit_code=$?
    local line_number=$1
    log_and_echo "ERROR: Script failed at line $line_number with exit code $exit_code"
    log_and_echo "ERROR: Last command: $BASH_COMMAND"
    log_and_echo "ERROR: Installation failed. Check the log file: $(get_log_file)"
    echo "Press Enter to exit..."
    read -r
    exit $exit_code
}

# Set up error trap
trap 'handle_error $LINENO' ERR

log_and_echo "========= $PACKAGE_NAME Build Script ========="
log_and_echo "Starting installation process..."
log_and_echo "Log file: $(get_log_file)"
safe_ensure_python_installed 3 13
check_and_create_venv
safe_activate_venv
upgrade_pip
install_local_dependencies
python_cmd=$(get_python_command)
python_version=$("$python_cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>/dev/null || echo "Unknown")
log_and_echo "========= Build Summary ========="
log_and_echo "Python version: $python_version"
log_and_echo "Virtual environment: $VIRTUAL_ENV"
log_and_echo "Installed packages:"
get_installed_packages || log_and_echo "Warning: Could not list installed packages"
log_and_echo "========= Setting up Git hooks ========="
"$python_cmd" utils/setup_hooks.py
log_and_echo "========= Installation Complete ========="
log_and_echo "Installation completed successfully!"
log_and_echo "Log saved to: $(get_log_file)"
echo "Press Enter to continue..."
read -r
