#!/bin/bash
# Install functions script for Pyrox development environment
# This script contains all the utility functions used by install.sh

# Change to script directory
cd "$(dirname "$0")"

# Enable strict error handling
set -e  # Exit on any error
set -u  # Exit on undefined variables
set -o pipefail  # Exit on pipe failures

# Global variable to store the log file path
LOG_FILE=""

# Function to activate a virtual environment
activate_venv() {
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows/Git Bash
        source .venv/Scripts/activate
        
        # Set TCL_LIBRARY and TK_LIBRARY for tkinter support on Windows
        # Virtual environments don't include Tcl/Tk files, they use the base Python installation
        if [ -f ".venv/pyvenv.cfg" ]; then
            local python_home=$(grep "^home" .venv/pyvenv.cfg | cut -d'=' -f2 | tr -d ' ')
            if [ -d "$python_home/tcl/tcl8.6" ]; then
                export TCL_LIBRARY="$python_home/tcl/tcl8.6"
                log_and_echo "✓ Set TCL_LIBRARY=$TCL_LIBRARY"
            fi
            if [ -d "$python_home/tcl/tk8.6" ]; then
                export TK_LIBRARY="$python_home/tcl/tk8.6"
                log_and_echo "✓ Set TK_LIBRARY=$TK_LIBRARY"
            fi
        fi
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
        local python_cmd=$(get_python_command)
        log_and_echo "Using Python command: $python_cmd"
        
        if "$python_cmd" -m venv .venv 2>&1 | while IFS= read -r line; do
            log_and_echo "$line"
        done; then
            log_and_echo "✓ Virtual environment created"
        else
            log_error "Failed to create virtual environment"
            return 1
        fi
    else
        log_and_echo "✓ Virtual environment exists"
    fi
}

# Function to check if the required Python version is installed
# Parameter 1: Required major version (e.g., 3)
# Parameter 2: Required minor version (e.g., 13)
# Parameter 3: Required micro version (e.g., 9)
check_python_version_installed() {
    local required_version_major="$1"
    local required_version_minor="$2"
    local required_version_micro="$3"
    local python_version
    local required_version="${required_version_major}.${required_version_minor}.${required_version_micro}"

    log_and_echo "Checking Python version (required: ${required_version})..."
    
    # Try to get Python version with better error handling
    if python_version=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>&1); then
        log_and_echo "Current Python version: $python_version"
    else
        log_error "Unable to determine Python version"
        log_and_echo "Python version check output: $python_version"
        return 1
    fi

    # Check if version meets requirements
    if python -c "import sys; exit(0 if sys.version_info >= ($required_version_major, $required_version_minor, $required_version_micro) else 1)" 2>/dev/null; then
        log_and_echo "✓ Python $python_version meets requirements (${required_version}+)"
        return 0
    else
        log_error "Python ${required_version}+ is required. Found: $python_version"
        log_and_echo "Please install Python ${required_version} or higher"
        return 2
    fi
}

# Function to ensure Python is installed with prompt for auto-install
# Parameter 1: Required major version (e.g., 3)
# Parameter 2: Required minor version (e.g., 13)
# Parameter 3: Required micro version (e.g., 9)
ensure_python_installed() {
    local required_major="$1"
    local required_minor="$2"
    local required_micro="$3"
    
    # First check if Python is already installed and meets requirements
    if verify_python_installation "$required_major" "$required_minor" "$required_micro"; then
        return 0
    fi
    
    # If not, prompt for installation
    prompt_and_install_python "$required_major" "$required_minor" "$required_micro"
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    # Verify the installation
    verify_python_installation "$required_major" "$required_minor" "$required_micro"
    return $?
}

# Function to get username safely across different environments
get_username() {
    echo "${USER:-${USERNAME:-$(whoami 2>/dev/null || echo 'DefaultUser')}}"
}

# Function to get the working Python command
get_python_command() {
    # Try different Python commands in order of preference
    local python_commands=("python" "python3" "py")
    local python_paths=(
        "/c/Program Files/Python313/python.exe"
        "/c/Program Files/Python312/python.exe"
        "/c/Users/$(get_username)/AppData/Local/Programs/Python/Python313/python.exe"
        "/c/Users/$(get_username)/AppData/Local/Programs/Python/Python312/python.exe"
    )
    
    # First try command-based approach
    for cmd in "${python_commands[@]}"; do
        if command -v "$cmd" &> /dev/null && "$cmd" --version &> /dev/null 2>&1; then
            # Make sure it's not the Microsoft Store version
            local version_output=$("$cmd" --version 2>&1)
            if [[ "$version_output" != *"Microsoft Store"* ]]; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    
    # If commands don't work, try direct paths
    for path in "${python_paths[@]}"; do
        if [ -f "$path" ] && "$path" --version &> /dev/null 2>&1; then
            echo "$path"
            return 0
        fi
    done
    
    # Fallback to python (might fail)
    echo "python"
    return 1
}

# Function to print installed packages from a python environment
get_installed_packages() {
    local python_cmd=$(get_python_command)
    "$python_cmd" -m pip list --format=columns 2>&1 | while IFS= read -r line; do
        log_and_echo "$line"
    done
}

# Function to get the current log file path (utility function)
get_log_file() {
    echo "$LOG_FILE"
}

# Error handling function
# Parameter 1: Line number where the error occurred
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

# Function to install local dependencies from requirements.txt or pyproject.toml
install_local_dependencies() {
    local python_cmd=$(get_python_command)
    log_and_echo "Using Python command for dependencies: $python_cmd"
    
    if [ -f "requirements.txt" ]; then
        log_and_echo "Installing requirements from requirements.txt..."
        if "$python_cmd" -m pip install -r requirements.txt --upgrade 2>&1 | while IFS= read -r line; do
            log_and_echo "$line"
        done; then
            log_and_echo "✓ Requirements installed from requirements.txt"
        else
            log_error "Failed to install requirements from requirements.txt"
            return 1
        fi
    else
        log_and_echo "Warning: requirements.txt not found"
    fi

    if [ -f "pyproject.toml" ]; then
        log_and_echo "Installing package from pyproject.toml..."
        if "$python_cmd" -m pip install -e . --upgrade 2>&1 | while IFS= read -r line; do
            log_and_echo "$line"
        done; then
            log_and_echo "✓ Package installed from pyproject.toml"
        else
            log_error "Failed to install package from pyproject.toml"
            return 1
        fi
    else
        log_and_echo "Warning: pyproject.toml not found, skipping package installation"
    fi
}

# Function to automatically install Python
# Parameter 1: Required major version (e.g., 3)
# Parameter 2: Required minor version (e.g., 13)
# Parameter 3: Required micro version (e.g., 9)
install_python_automatically() {
    local required_major="$1"
    local required_minor="$2"
    local required_micro="$3"
    local python_version="${required_major}.${required_minor}.${required_micro}"
    
    log_and_echo "Detecting operating system..."
    
    # Detect operating system
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
        install_python_windows "$python_version"
        return $?
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        install_python_macos "$python_version"
        return $?
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        install_python_linux "$python_version"
        return $?
    else
        log_and_echo "Error: Unsupported operating system: $OSTYPE"
        return 1
    fi
}

# Function to install Python on Linux
# Parameter 1: Python version (e.g., 3.13.9)
install_python_linux() {
    local version="$1"
    local major_minor="${version}"
    
    log_and_echo "Installing Python ${version} on Linux..."
    
    # Detect Linux distribution
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        log_and_echo "Detected Debian/Ubuntu system. Installing via apt..."
        sudo apt-get update 2>&1 | while IFS= read -r line; do
            log_and_echo "$line"
        done
        sudo apt-get install -y python${major_minor} python${major_minor}-venv python${major_minor}-pip 2>&1 | while IFS= read -r line; do
            log_and_echo "$line"
        done
        
        # Create symlink if needed
        if [ ! -L "/usr/bin/python" ]; then
            sudo ln -sf "/usr/bin/python${major_minor}" /usr/bin/python
        fi
        
    elif command -v yum &> /dev/null; then
        # RHEL/CentOS/Fedora
        log_and_echo "Detected RHEL/CentOS/Fedora system. Installing via yum..."
        sudo yum install -y python${major_minor} python${major_minor}-pip 2>&1 | while IFS= read -r line; do
            log_and_echo "$line"
        done
        
    elif command -v dnf &> /dev/null; then
        # Fedora (newer versions)
        log_and_echo "Detected Fedora system. Installing via dnf..."
        sudo dnf install -y python${major_minor} python${major_minor}-pip 2>&1 | while IFS= read -r line; do
            log_and_echo "$line"
        done
        
    elif command -v pacman &> /dev/null; then
        # Arch Linux
        log_and_echo "Detected Arch Linux system. Installing via pacman..."
        sudo pacman -S --noconfirm python 2>&1 | while IFS= read -r line; do
            log_and_echo "$line"
        done
        
    else
        log_and_echo "Error: Unsupported Linux distribution or package manager not found"
        log_and_echo "Please install Python ${version} manually using your distribution's package manager"
        return 1
    fi
    
    log_and_echo "✓ Python installation completed"
    return 0
}

# Function to install Python on macOS
# Parameter 1: Python version (e.g., 3.13.9)
install_python_macos() {
    local version="$1"
    
    log_and_echo "Installing Python ${version} on macOS..."
    
    # Check if Homebrew is available
    if command -v brew &> /dev/null; then
        log_and_echo "Using Homebrew to install Python..."
        brew install python@${version} 2>&1 | while IFS= read -r line; do
            log_and_echo "$line"
        done
        
        # Create symlinks if needed
        if [ ! -L "/usr/local/bin/python" ]; then
            ln -sf "/usr/local/bin/python${version}" /usr/local/bin/python
        fi
        
        log_and_echo "✓ Python installation completed via Homebrew"
        return 0
    fi
    
    # Fallback: Download from python.org
    log_and_echo "Homebrew not available. Please install Homebrew first or download Python manually from:"
    log_and_echo "https://www.python.org/downloads/macos/"
    return 1
}

# Function to install Python on Windows
# Parameter 1: Python version (e.g., 3.13.9)
install_python_windows() {
    local version="$1"
    local latest_patch_version
    local version_nodot="${version//./}"  # e.g., 3.13 -> 3139    
    log_and_echo "Installing Python ${version} on Windows..."

    # Get the latest patch version (e.g., 3.13.9)
    latest_patch_version=$(curl -s "https://www.python.org/api/v2/downloads/release/?is_published=true&content_type__model=release&version__startswith=${version}" | 
                          grep -o '"version":"[^"]*"' | head -1 | sed 's/"version":"\([^"]*\)"/\1/')
    
    if [ -z "$latest_patch_version" ]; then
        latest_patch_version="${version}"  # Fallback
    fi
    
    local installer_url="https://www.python.org/ftp/python/${latest_patch_version}/python-${latest_patch_version}-amd64.exe"
    local installer_file="python-${latest_patch_version}-installer.exe"
    
    log_and_echo "Downloading Python ${latest_patch_version} installer..."
    if ! curl -L -o "$installer_file" "$installer_url" 2>&1 | while IFS= read -r line; do
        log_and_echo "curl: $line"
    done; then
        log_error "Failed to download Python installer from $installer_url"
        return 1
    fi
    
    if [ ! -f "$installer_file" ]; then
        log_error "Python installer file not found after download"
        return 1
    fi
    
    log_and_echo "Running Python installer (this may take a few minutes)..."
    log_and_echo "Installer command: ./$installer_file /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_doc=0 Include_tcltk=1 Include_launcher=1 AssociateFiles=1"
    
    # Run installer and capture exit code
    if "./$installer_file" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_doc=0 Include_tcltk=1 Include_launcher=1 AssociateFiles=1; then
        log_and_echo "✓ Python installer completed successfully"
    else
        local install_result=$?
        log_and_echo "Warning: Installer returned exit code: $install_result (this may be normal)"
    fi
    
    # Clean up installer
    rm -f "$installer_file"
    log_and_echo "Cleaned up installer file"
    
    # Refresh PATH for current session - try multiple common locations
    local username=$(get_username)
    local python_dirs=(
        "/c/Program Files/Python${version_nodot}"
        "/c/Program Files/Python${version_nodot}/Scripts"
        "/c/Users/$username/AppData/Local/Programs/Python/Python${version_nodot}"
        "/c/Users/$username/AppData/Local/Programs/Python/Python${version_nodot}/Scripts"
    )
    
    for dir in "${python_dirs[@]}"; do
        if [ -d "$dir" ] && [[ ":$PATH:" != *":$dir:"* ]]; then
            export PATH="$dir:$PATH"
            log_and_echo "Added to PATH: $dir"
        fi
    done
    
    # Update PATH
    update_windows_path_for_python "$version"
    log_and_echo "✓ Python installation completed"
    return 0
}

# Function to log and display messages
# Parameter 1: Message string to log and echo
log_and_echo() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Check if logging has been setup
    if [ -z "$LOG_FILE" ]; then
        echo "WARNING: Logging not setup. Call setup_logging first."
        echo "$message"
        return 1
    fi
    
    # Log and echo the message with timestamp
    echo "[$timestamp] $message" | tee -a "$LOG_FILE"
    
    return 0
}

# Function to execute a command and log both stdout and stderr
# Parameter 1: Command description
# Parameters 2+: Command and arguments
log_and_execute() {
    local description="$1"
    shift
    local command="$*"
    
    log_and_echo "Executing: $description"
    log_and_echo "Command: $command"
    
    # Execute command and capture both stdout and stderr
    if eval "$command" 2>&1 | while IFS= read -r line; do
        log_and_echo "$line"
    done; then
        log_and_echo "✓ $description completed successfully"
        return 0
    else
        local exit_code=${PIPESTATUS[0]}
        log_error "$description failed with exit code: $exit_code"
        return $exit_code
    fi
}

# Function to log error messages
# Parameter 1: Error message string to log and echo
log_error() {
    local error_message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Check if logging has been setup
    if [ -z "$LOG_FILE" ]; then
        echo "ERROR: Logging not setup. Call setup_logging first." >&2
        echo "ERROR: $error_message" >&2
        return 1
    fi
    
    # Log and echo the error message with timestamp to both stdout and stderr
    echo "[$timestamp] ERROR: $error_message" | tee -a "$LOG_FILE" >&2
    
    return 0
}

# Function to prompt user and install Python automatically
# Parameter 1: Required major version (e.g., 3)
# Parameter 2: Required minor version (e.g., 13)
# Parameter 3: Required micro version (e.g., 9)
prompt_and_install_python() {
    local required_major="$1"
    local required_minor="$2"
    local required_micro="$3"
    local required_version="${required_major}.${required_minor}.${required_micro}"
    
    # Validate parameters
    if [ -z "$required_major" ] || [ -z "$required_minor" ] || [ -z "$required_micro"]; then
        log_and_echo "Error: prompt_and_install_python requires major, minor and micro version numbers"
        return 1
    fi
    
    # Prompt user for installation
    log_and_echo "Python ${required_version} is required for this project."
    log_and_echo ""
    log_and_echo "Would you like to automatically download and install Python ${required_version}? (y/N)"
    read -p "Enter your choice: " choice
    
    case "$choice" in 
        [yY]|[yY][eE][sS])
            log_and_echo "Installing Python ${required_version}..."
            if install_python_automatically "$required_major" "$required_minor" "$required_micro"; then
                log_and_echo "✓ Python installation process completed"
                return 0
            else
                log_error "Python installation failed or was cancelled"
                return 1
            fi
            ;;
        *)
            log_and_echo "Installation cancelled. Please install Python ${required_version}+ manually."
            log_and_echo "Visit: https://www.python.org/downloads/"
            return 1
            ;;
    esac
}

# Function to safety activate virtual environment
safe_activate_venv() {
    activate_venv
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

# Function to safety exit if python is not installed with prompt for auto-install
# Parameter 1: Required major version (e.g., 3)
# Parameter 2: Required minor version (e.g., 13)
# Parameter 3: Required micro version (e.g., 9)
safe_ensure_python_installed() {
    local required_major="$1"
    local required_minor="$2"
    local required_micro="$3"

    log_and_execute "Ensuring Python ${required_major}.${required_minor}.${required_micro}+ is installed" ensure_python_installed "$required_major" "$required_minor" "$required_micro"
    if [ $? -ne 0 ]; then
        log_and_echo "Error: Python installation failed or was cancelled."
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
    local python_cmd=$(get_python_command)
    log_and_echo "Using Python command: $python_cmd"
    
    if "$python_cmd" -m pip install --upgrade pip 2>&1 | while IFS= read -r line; do
        log_and_echo "$line"
    done; then
        log_and_echo "✓ pip upgraded successfully"
        return 0
    else
        log_error "Failed to upgrade pip"
        return 1
    fi
}

# Function to update Windows PATH for Python
# Parameter 1: Python version (e.g., 3.13.9)
update_windows_path_for_python() {
    local version="$1"
    log_and_echo "Updating Windows PATH for Python..."
    
    # Get username safely
    local username=$(get_username)
    log_and_echo "Using username: $username"
    
    local version_nodot="${version//./}"  # e.g., 3.13 -> 3139
    local python_dirs=(
        "C:\\Users\\$username\\AppData\\Local\\Programs\\Python\\Python${version_nodot}"
        "C:\\Users\\$username\\AppData\\Local\\Programs\\Python\\Python${version_nodot}\\Scripts"
        "C:\\Program Files\\Python${version_nodot}"
        "C:\\Program Files\\Python${version_nodot}\\Scripts"
    )
    
    # Use PowerShell to update the PATH persistently for the current user
    for dir in "${python_dirs[@]}"; do
        # Convert to Windows path format
        local win_dir=$(echo "$dir" | sed "s|\\$username|$username|g")
        
        # Check if directory exists (convert back to Unix format for test)
        local unix_dir=$(echo "$win_dir" | sed 's|C:|/c|g' | sed 's|\\|/|g')
        if [ -d "$unix_dir" ]; then
            log_and_echo "Adding $win_dir to Windows PATH..."
            
            # Use PowerShell to add to user PATH if not already there
            powershell.exe -Command "
                \$currentPath = [Environment]::GetEnvironmentVariable('Path', 'User')
                if (\$currentPath -notlike '*$win_dir*') {
                    \$newPath = \$currentPath + ';$win_dir'
                    [Environment]::SetEnvironmentVariable('Path', \$newPath, 'User')
                    Write-Host 'Added $win_dir to user PATH'
                } else {
                    Write-Host '$win_dir already in PATH'
                }
            " 2>&1 | while IFS= read -r line; do
                log_and_echo "PowerShell: $line"
            done
            
            # Also add to current session PATH
            if [[ ":$PATH:" != *":$unix_dir:"* ]]; then
                export PATH="$unix_dir:$PATH"
                log_and_echo "Added to current session PATH: $unix_dir"
            fi
        fi
    done
    
    log_and_echo "✓ Windows PATH update completed"
}

# Function to verify Python installation after auto-install
# Parameter 1: Required major version (e.g., 3)
# Parameter 2: Required minor version (e.g., 13)
# Parameter 3: Required micro version (e.g., 9)
verify_python_installation() {
    log_and_echo "Verifying Python installation..."
    local required_major="$1"
    local required_minor="$2"
    local required_micro="$3"
    local working_python_cmd=""
    
    # Give the system a moment to update PATH
    sleep 2
    
    # Try to find python in common locations
    log_and_echo "Searching for Python executable..."
    local username=$(get_username)
    log_and_echo "Using username: $username"
    local python_paths=(
        "python"
        "python3"
        "python${required_major}.${required_minor}.${required_micro}"
        "/usr/local/bin/python${required_major}.${required_minor}.${required_micro}"
        "/usr/bin/python${required_major}.${required_minor}.${required_micro}"
        "/c/Program Files/Python${required_major}${required_minor}.${required_micro}/python.exe"
        "/c/Users/$username/AppData/Local/Programs/Python/Python${required_major}${required_minor}.${required_micro}/python.exe"
    )
    
    # For Windows, also check actual file existence since command -v may not work with paths
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
        # Check direct file paths first on Windows
        local windows_paths=(
            "/c/Program Files/Python${required_major}${required_minor}/python.exe"
            "/c/Users/$username/AppData/Local/Programs/Python/Python${required_major}${required_minor}/python.exe"
            "/c/Python${required_major}${required_minor}/python.exe"
        )
        
        for python_path in "${windows_paths[@]}"; do
            if [ -f "$python_path" ]; then
                log_and_echo "Found Python executable at: $python_path"
                if "$python_path" -c "import sys; exit(0 if sys.version_info >= ($required_major, $required_minor, $required_micro) else 1)" 2>/dev/null; then
                    local version=$("$python_path" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>/dev/null)
                    log_and_echo "✓ Python ${version} verified and working"
                    working_python_cmd="$python_path"
                    break
                fi
            fi
        done
    fi
    
    # If we haven't found a working Python yet, try the command approach
    if [ -z "$working_python_cmd" ]; then
        for python_cmd in "${python_paths[@]}"; do
            # Skip the 'python' command on Windows due to Microsoft Store alias issues
            if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]] && [[ "$python_cmd" == "python" ]]; then
                continue
            fi
            
            if command -v "$python_cmd" &> /dev/null; then
                if "$python_cmd" -c "import sys; exit(0 if sys.version_info >= ($required_major, $required_minor, $required_micro) else 1)" 2>/dev/null; then
                    local version=$("$python_cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>/dev/null)
                    log_and_echo "✓ Python ${version} verified and working"
                    working_python_cmd="$python_cmd"
                    break
                fi
            fi
        done
    fi
    
    # If we didn't find a working python command, fail
    if [ -z "$working_python_cmd" ]; then
        log_and_echo "Error: Python installation verification failed"
        return 1
    fi
    
    # Create alias if the working command is not 'python'
    if [ "$working_python_cmd" != "python" ]; then
        log_and_echo "Creating 'python' alias for '$working_python_cmd'..."
        
        # For Windows/Git Bash, create a function and try to add to PATH
        if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
            # Create a wrapper function for the current session
            eval "python() { \"$working_python_cmd\" \"\$@\"; }"
            export -f python 2>/dev/null || true
            log_and_echo "✓ Created 'python' function for current session"
            
            # Add Python directory to PATH if it's a full path
            if [[ "$working_python_cmd" == *"/"* ]]; then
                local python_dir=$(dirname "$working_python_cmd")
                if [[ ":$PATH:" != *":$python_dir:"* ]]; then
                    export PATH="$python_dir:$PATH"
                    log_and_echo "✓ Added Python directory to PATH: $python_dir"
                fi
                
                # Try to create a symlink in a user directory for persistence
                local user_bin="$HOME/.local/bin"
                mkdir -p "$user_bin"
                
                # Create a batch file wrapper for Windows
                cat > "$user_bin/python.bat" << EOF

@echo off
"$working_python_cmd" %*
EOF
                chmod +x "$user_bin/python.bat"
                
                # Add user bin to PATH if not already there
                if [[ ":$PATH:" != *":$user_bin:"* ]]; then
                    export PATH="$user_bin:$PATH"
                    log_and_echo "✓ Created python.bat in $user_bin and added to PATH"
                fi
            fi
        else
            # For Unix-like systems, try to create a symlink
            local link_target="/usr/local/bin/python"
            if [ -w "/usr/local/bin" ]; then
                ln -sf "$working_python_cmd" "$link_target" 2>/dev/null || true
                log_and_echo "✓ Created symlink: $link_target -> $working_python_cmd"
            else
                # Create in a user-writable location
                local user_bin="$HOME/.local/bin"
                mkdir -p "$user_bin"
                ln -sf "$working_python_cmd" "$user_bin/python" 2>/dev/null || true
                
                # Add to PATH if not already there
                if [[ ":$PATH:" != *":$user_bin:"* ]]; then
                    export PATH="$user_bin:$PATH"
                    log_and_echo "✓ Created symlink in $user_bin and added to PATH"
                fi
            fi
        fi
    fi
    
    # Final verification that 'python' command now works
    if command -v python &> /dev/null; then
        if python -c "import sys; exit(0 if sys.version_info >= ($required_major, $required_minor, $required_micro) else 1)" 2>/dev/null; then
            local final_version=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>/dev/null)
            log_and_echo "✓ 'python' command verified: Python ${final_version}"
            return 0
        fi
    fi
    
    log_and_echo "Warning: Python is installed but 'python' command may not be available in new terminals"
    log_and_echo "You may need to restart your terminal or use '$working_python_cmd' directly"
    return 0  # Don't fail here since Python is actually installed and working
}
