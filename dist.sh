#!/bin/bash
# filepath: c:\Users\MH8243\EQUANS\Indicon LLC - Software & Emulation - Documents\Pyrox\dist.sh

# Configuration
SOURCE_DIR="./dist/Pyrox"
DESTINATION_SERVER="S:\STH1\Indicon\Jobs\Software\Physirox\Pyrox"

# Logging Configuration
LOG_DIR="./logs"
LOG_FILE="$LOG_DIR/dist_$(date +%Y%m%d_%H%M%S).log"
LATEST_LOG="$LOG_DIR/dist_latest.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output and log
log_and_print() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Print to console with colors
    case "$level" in
        "INFO")
            echo -e "${GREEN}[INFO]${NC} $message"
            ;;
        "WARNING")
            echo -e "${YELLOW}[WARNING]${NC} $message"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} $message"
            ;;
        "DEBUG")
            echo -e "${BLUE}[DEBUG]${NC} $message"
            ;;
        *)
            echo "$message"
            ;;
    esac
    
    # Log to file (without colors)
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# Function wrappers for easier use
print_status() {
    log_and_print "INFO" "$1"
}

print_warning() {
    log_and_print "WARNING" "$1"
}

print_error() {
    log_and_print "ERROR" "$1"
}

print_debug() {
    log_and_print "DEBUG" "$1"
}

# Setup logging
setup_logging() {
    # Create log directory if it doesn't exist
    mkdir -p "$LOG_DIR"
    
    # Create log file and add header
    {
        echo "==============================================="
        echo "Pyrox Distribution/Deployment Log"
        echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "User: $(whoami)"
        echo "Working Directory: $(pwd)"
        echo "Source: $SOURCE_DIR"
        echo "Destination: $DESTINATION_SERVER"
        echo "==============================================="
        echo ""
    } > "$LOG_FILE"
    
    # Create symlink to latest log
    ln -sf "$(basename "$LOG_FILE")" "$LATEST_LOG" 2>/dev/null || cp "$LOG_FILE" "$LATEST_LOG"
    
    print_debug "Logging initialized: $LOG_FILE"
}

# Cleanup function
cleanup() {
    local exit_code=$?
    print_status "Distribution/deployment process finished with exit code: $exit_code"
    
    # Add footer to log
    {
        echo ""
        echo "==============================================="
        echo "Process completed: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "Exit code: $exit_code"
        echo "Total duration: $((SECONDS))s"
        echo "==============================================="
    } >> "$LOG_FILE"
    
    if [ $exit_code -eq 0 ]; then
        print_status "Distribution/deployment completed successfully!"
        print_status "Log file: $LOG_FILE"
    else
        print_error "Distribution/deployment failed! Check log file: $LOG_FILE"
    fi
    
    exit $exit_code
}

# Set trap for cleanup
trap cleanup EXIT

# Start logging and timer
SECONDS=0
setup_logging

print_status "Starting Pyrox distribution/deployment..."

# Check if source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    print_error "Source directory '$SOURCE_DIR' does not exist!"
    print_error "Please run your build/deploy process first."
    exit 1
fi

print_status "Source directory verified: $SOURCE_DIR"

# Log source directory contents
print_debug "Source directory contents:"
ls -la "$SOURCE_DIR" 2>&1 | tee -a "$LOG_FILE"

# Calculate source size
SOURCE_SIZE=$(du -sh "$SOURCE_DIR" 2>/dev/null | cut -f1 || echo "Unknown")
print_status "Source directory size: $SOURCE_SIZE"

# Validate destination format
if [[ "$DESTINATION_SERVER" == *"user@hostname"* ]]; then
    print_error "Please update the DESTINATION_SERVER variable with your actual server details!"
    print_error "Format: user@hostname:/path/to/destination"
    print_error "Example: admin@myserver.com:/opt/pyrox/"
    exit 1
fi

print_status "Source: $SOURCE_DIR"
print_status "Destination: $DESTINATION_SERVER"

# Create destination directory if it doesn't exist
mkdir -p "$DESTINATION_SERVER" 2>&1 | tee -a "$LOG_FILE"

# Perform local copy
print_status "Copying Pyrox files (local)..."
cp -r "$SOURCE_DIR"/* "$DESTINATION_SERVER/" 2>&1 | tee -a "$LOG_FILE"

# Check if deployment was successful
if [ $? -eq 0 ]; then
    print_status "Deployment completed successfully!"
    print_status "Pyrox has been deployed to: $DESTINATION_SERVER"
    
    ls -la "$DESTINATION_SERVER" 2>&1 | tee -a "$LOG_FILE"
    
    DEST_SIZE=$(du -sh "$DESTINATION_SERVER" 2>/dev/null | cut -f1 || echo "Unknown")
    print_status "Destination directory size: $DEST_SIZE"
    
else
    print_error "Deployment failed!"
    print_error "Please check the error messages above and log file: $LOG_FILE"
    exit 1
fi

print_status "Deployment process completed successfully!"
print_status "Total time: ${SECONDS}s"