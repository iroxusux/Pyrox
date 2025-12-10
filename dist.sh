#!/bin/bash

# Source utilities
source ./utils.sh

# Pyrox Build Script
# This script sets up the development environment and installs dependencies

# Setup logging
setup_logging "logs" "dist"

# Configuration
PACKAGE_NAME="Pyrox"
PACKAGE_NAME_LOWER="pyrox"

# Configuration
SOURCE_DIR="./dist/Pyrox"
DESTINATION_SERVER="S:\STH1\Company\Jobs\Software\Physirox\Pyrox"

# Cleanup function
cleanup() {
    local exit_code=$?
    log_and_echo "Distribution/deployment process finished with exit code: $exit_code"
    log_and_echo ""
    log_and_echo "==============================================="
    log_and_echo "Process completed: $(date '+%Y-%m-%d %H:%M:%S')"
    log_and_echo "Exit code: $exit_code"
    log_and_echo "Total duration: $((SECONDS))s"
    log_and_echo "==============================================="

    
    if [ $exit_code -eq 0 ]; then
        log_and_echo "Distribution/deployment completed successfully!"
    else
        log_and_echo "Distribution/deployment failed! Check log file!"
    fi
    
    exit $exit_code
}

# Set trap for cleanup
trap cleanup EXIT

# Start logging and timer
SECONDS=0

log_and_echo "Starting Pyrox distribution/deployment..."

# Check if source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    log_and_echo "Source directory '$SOURCE_DIR' does not exist!"
    log_and_echo "Please run your build/deploy process first."
    exit 1
fi

log_and_echo "Source directory verified: $SOURCE_DIR"

# Log source directory contents
log_and_echo "Source directory contents:"
ls -la "$SOURCE_DIR" 2>&1 | tee -a "$LOG_FILE"

# Calculate source size
SOURCE_SIZE=$(du -sh "$SOURCE_DIR" 2>/dev/null | cut -f1 || echo "Unknown")
log_and_echo "Source directory size: $SOURCE_SIZE"

# Validate destination format
if [[ "$DESTINATION_SERVER" == *"user@hostname"* ]]; then
    log_and_echo "Please update the DESTINATION_SERVER variable with your actual server details!"
    log_and_echo "Format: user@hostname:/path/to/destination"
    log_and_echo "Example: admin@myserver.com:/opt/pyrox/"
    exit 1
fi

log_and_echo "Source: $SOURCE_DIR"
log_and_echo "Destination: $DESTINATION_SERVER"

# Create destination directory if it doesn't exist
mkdir -p "$DESTINATION_SERVER" 2>&1 | tee -a "$LOG_FILE"

# Perform local copy
log_and_echo "Copying Pyrox files (local)..."
cp -r "$SOURCE_DIR"/* "$DESTINATION_SERVER/" 2>&1 | tee -a "$LOG_FILE"

# Check if deployment was successful
if [ $? -eq 0 ]; then
    log_and_echo "Deployment completed successfully!"
    log_and_echo "Pyrox has been deployed to: $DESTINATION_SERVER"
    
    ls -la "$DESTINATION_SERVER" 2>&1 | tee -a "$LOG_FILE"
    
    DEST_SIZE=$(du -sh "$DESTINATION_SERVER" 2>/dev/null | cut -f1 || echo "Unknown")
    log_and_echo "Destination directory size: $DEST_SIZE"
    
else
    log_and_echo "Deployment failed!"
    log_and_echo "Please check the error messages above and log file: $LOG_FILE"
    exit 1
fi

log_and_echo "Deployment process completed successfully!"
log_and_echo "Total time: ${SECONDS}s"