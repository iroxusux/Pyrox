#!/bin/bash
# Install script for setting up the development environment and installing dependencies
# Configuration
PACKAGE_NAME="Pyrox"
PACKAGE_NAME_LOWER="pyrox"

# Change to script directory
cd "$(dirname "$0")"

# Source utilities
source ./utils.sh

# Setup logging
setup_logging "logs" "install"
log_and_echo "=== $PACKAGE_NAME Build Script ==="
log_and_echo "Starting installation process..."
safe_check_python_version_installed 3 13
check_and_create_venv
safe_activate_venv
upgrade_pip
install_local_dependencies
log_and_echo "=== Build Summary ==="
log_and_echo "Python version: $python_version"
log_and_echo "Virtual environment: $VIRTUAL_ENV"
log_and_echo "Installed packages:"
get_installed_packages
log_and_echo "=== Installation Complete ==="
read -p "Press Enter to continue..."
