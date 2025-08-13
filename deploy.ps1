# Create logs directory if it doesn't exist
if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs"
}

# Set log file with timestamp
$LOG_FILE = "logs/deploy_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# Function to log and display messages
function Log-And-Echo {
    param($Message, $Color = "White")
    Write-Host $Message -ForegroundColor $Color
    Add-Content -Path $LOG_FILE -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'): $Message"
}

# Start transcript to capture all output
Start-Transcript -Path $LOG_FILE -Append

Log-And-Echo "=== Starting Pyrox Deployment ===" "Green"
Log-And-Echo "Log file: $LOG_FILE" "Cyan"
Log-And-Echo "Timestamp: $(Get-Date)"

# Clean up previous builds
Log-And-Echo "Cleaning up previous builds..." "Yellow"
if (Test-Path "dist") {
    Remove-Item "dist" -Recurse -Force -ErrorAction SilentlyContinue
}
if (Test-Path "build") {
    Remove-Item "build" -Recurse -Force -ErrorAction SilentlyContinue
}
if (Test-Path "*.spec") {
    Remove-Item "*.spec" -Force -ErrorAction SilentlyContinue
}

# Stop any running Pyrox processes
Log-And-Echo "Stopping any running Pyrox processes..." "Yellow"
Stop-Process -Name "Pyrox" -Force -ErrorAction SilentlyContinue

# Run the build script
Log-And-Echo "Running build script..." "Yellow"
& ".\build.sh"
if ($LASTEXITCODE -ne 0) {
    Log-And-Echo "ERROR: Build script failed!" "Red"
    Stop-Transcript
    exit 1
}

# Run PyInstaller with improved error handling
Log-And-Echo "Running PyInstaller..." "Yellow"
$pyinstallerArgs = @(
    "--name", "Pyrox",
    "--noconfirm",
    "--noconsole", 
    "--onedir",
    "--icon=pyrox/ui/icons/_def.ico",
    "--add-data", "pyrox/ui/icons;pyrox/ui/icons",
    "--add-data", "pyrox/tasks;pyrox/tasks", 
    "--add-data", "pyrox/applications/mod;pyrox/applications/mod",
    "--add-data", "docs/controls;docs/controls",
    "--distpath", "dist",
    "--workpath", "build",
    "--clean",
    "pyrox/__main__.py"
)

try {
    & pyinstaller @pyinstallerArgs
    if ($LASTEXITCODE -eq 0) {
        Log-And-Echo "Build completed successfully!" "Green"
        Log-And-Echo "Executable location: dist\Pyrox\Pyrox.exe" "Cyan"
        
        # Set proper permissions on the dist directory
        icacls "dist" /grant "$env:USERNAME:(OI)(CI)F" /T | Out-Null
        
        Log-And-Echo "Permissions set successfully." "Green"
        Log-And-Echo "Log saved to: $LOG_FILE" "Cyan"
    }
    else {
        Log-And-Echo "Build failed with errors." "Red"
        Log-And-Echo "Check log file for details: $LOG_FILE" "Red"
        Stop-Transcript
        exit 1
    }
}
catch {
    Log-And-Echo "Error running PyInstaller: $($_.Exception.Message)" "Red"
    Log-And-Echo "Check log file for details: $LOG_FILE" "Red"
    Stop-Transcript
    exit 1
}

Log-And-Echo "=== Deployment Complete ===" "Green"
Stop-Transcript
Read-Host "Press Enter to continue..."