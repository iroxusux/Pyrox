#!/bin/bash

# Create logs directory if it doesn't exist
mkdir -p logs

# Set log file with timestamp
LOG_FILE="logs/deploy_$(date +%Y%m%d_%H%M%S).log"

# Function to log and display messages
log_and_echo() {
    echo "$1" | tee -a "$LOG_FILE"
}

log_and_echo "=== Starting Pyrox Deployment ==="
log_and_echo "Log file: $LOG_FILE"
log_and_echo "Timestamp: $(date)"

# Clean up previous builds
log_and_echo "Cleaning up previous builds..."
rm -rf dist/ build/ *.spec

# Stop any running Pyrox processes
log_and_echo "Stopping any running Pyrox processes..."
pkill -f "Pyrox" 2>/dev/null || true

# Run the build script
log_and_echo "Running build script..."
source ./build.sh
if [ $? -ne 0 ]; then
    log_and_echo "ERROR: Build script failed!"
    exit 1
fi

# Run PyInstaller with improved error handling
log_and_echo "Running PyInstaller..."
pyinstaller --name "Pyrox" \
    --noconfirm \
    --onedir \
    --icon="pyrox/ui/icons/_def.ico" \
    --add-data "pyrox/ui/icons:pyrox/ui/icons" \
    --add-data "pyrox/tasks:pyrox/tasks" \
    --add-data "pyrox/applications/mod:pyrox/applications/mod" \
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
    pyrox/__main__.py

# Check if build was successful
if [ $? -eq 0 ]; then
    log_and_echo "Build completed successfully!"
    log_and_echo "Executable location: dist/Pyrox/Pyrox.exe"
    log_and_echo "Log saved to: $LOG_FILE"
else
    log_and_echo "ERROR: Build failed with errors."
    log_and_echo "Check log file for details: $LOG_FILE"
    exit 1
fi

log_and_echo "=== Deployment Complete ==="
read -p "Press Enter to continue..."