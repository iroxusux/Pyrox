#!/bin/bash

# Source utilities
source ./utils.sh

# Pyrox Build Script
# This script builds the package into a distributable format using PyInstaller

# Setup logging
setup_logging "logs" "build"

# Configuration
PACKAGE_NAME="Pyrox"
PACKAGE_NAME_LOWER="pyrox"

log_and_echo "=== Starting $PACKAGE_NAME Build Process ==="
log_and_echo "Log file: $LOG_FILE"
log_and_echo "Timestamp: $(date)"

# Clean up previous builds
log_and_echo "Cleaning up previous builds..."
rm -rf dist/ build/ *.spec

# Stop any running Pyrox processes
log_and_echo "Stopping any running $PACKAGE_NAME processes..."
pkill -f $PACKAGE_NAME 2>/dev/null || true

# Run PyInstaller with improved error handling
log_and_echo "Running PyInstaller..."
pyinstaller --name $PACKAGE_NAME \
    --noconfirm \
    --onedir \
    --icon="$PACKAGE_NAME/ui/icons/_def.ico" \
    --add-data "$PACKAGE_NAME/ui/icons:$PACKAGE_NAME/ui/icons" \
    --add-data "$PACKAGE_NAME/tasks:$PACKAGE_NAME/tasks" \
    --add-data "$PACKAGE_NAME/applications/mod:$PACKAGE_NAME/applications/mod" \
    --add-data "docs/controls:docs/controls" \
    --hidden-import="PIL" \
    --hidden-import="PIL.Image" \
    --hidden-import="PIL.ImageTk" \
    --hidden-import="tkinter" \
    --hidden-import="tkinter.colorchooser" \
    --hidden-import="tkinter.commondialog" \
    --hidden-import="tkinter.constants" \
    --hidden-import="tkinter.dialog" \
    --hidden-import="tkinter.dnd" \
    --hidden-import="tkinter.filedialog" \
    --hidden-import="tkinter.font" \
    --hidden-import="tkinter.messagebox" \
    --hidden-import="tkinter.scrolledtext" \
    --hidden-import="tkinter.simpledialog" \
    --hidden-import="tkinter.ttk" \
    --distpath dist \
    --workpath build \
    --clean \
    $PACKAGE_NAME_LOWER/__main__.py

# Check if build was successful
if [ $? -eq 0 ]; then
    log_and_echo "Build completed successfully!"
    log_and_echo "Executable location: dist/$PACKAGE_NAME/$PACKAGE_NAME.exe"
    log_and_echo "Log saved to: $LOG_FILE"
else
    log_and_echo "ERROR: Build failed with errors."
    log_and_echo "Check log file for details: $LOG_FILE"
    exit 1
fi

log_and_echo "=== Deployment Complete ==="
read -p "Press Enter to continue..."