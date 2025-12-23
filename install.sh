#!/bin/bash
# Install script for setting up the development environment and installing dependencies
# This script acts as the logic driver and sources all functions from install-functions.sh

# Source the functions script
SCRIPT_DIR="$(dirname "$0")"
source "$SCRIPT_DIR/install-functions.sh"

# Set package name
PACKAGE_NAME="Pyrox"
PACKAGE_NAME_LOWER="pyrox"

# Set up error trap
trap 'handle_error $LINENO' ERR

setup_logging "logs" "install"

log_and_echo "========= $PACKAGE_NAME Build Script ========="
log_and_echo "Starting installation process..."
log_and_echo "Log file: ${LOG_FILE}"
safe_ensure_python_installed 3 13 9
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
# Check to see if pyrox is installed in the venv site-packages or if we need to use a local utils path
if [ -f ".venv/Lib/site-packages/pyrox/__init__.py" ]; then
    log_and_echo "Using pyrox package from virtual environment site-packages for hook setup"
    "$python_cmd" .venv/Lib/site-packages/pyrox/utils/setup_hooks.py
else
    log_and_echo "Using local utils path for hook setup"
    "$python_cmd" pyrox/utils/setup_hooks.py
fi

log_and_echo "========= Installation Complete ========="
log_and_echo "Installation completed successfully!"
log_and_echo "Log saved to: $(get_log_file)"
echo "Press Enter to continue..."
read -r
