# PowerShell deployment script for Pyrox
Write-Host "Starting Pyrox deployment..." -ForegroundColor Green

# Clean up previous builds
Write-Host "Cleaning up previous builds..." -ForegroundColor Yellow
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
Write-Host "Stopping any running Pyrox processes..." -ForegroundColor Yellow
Stop-Process -Name "Pyrox" -Force -ErrorAction SilentlyContinue

# Run the build script
Write-Host "Running build script..." -ForegroundColor Yellow
& ".\build.sh"

# Run PyInstaller with improved error handling
Write-Host "Running PyInstaller..." -ForegroundColor Yellow
$pyinstallerArgs = @(
    "--name", "Pyrox",
    "--noconfirm",
    "--noconsole", 
    "--onedir",
    "--icon=pyrox/ui/icons/_def.ico",
    "--add-data", "pyrox/ui/icons;pyrox/ui/icons",
    "--add-data", "pyrox/tasks;pyrox/tasks", 
    "--add-data", "pyrox/applications/mod;pyrox/applications/mod",
    "--distpath", "dist",
    "--workpath", "build",
    "--clean",
    "__main__.py"
)

try {
    & pyinstaller @pyinstallerArgs
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Build completed successfully!" -ForegroundColor Green
        Write-Host "Executable location: dist\Pyrox\Pyrox.exe" -ForegroundColor Cyan
        
        # Set proper permissions on the dist directory
        icacls "dist" /grant "$env:USERNAME:(OI)(CI)F" /T | Out-Null
        
        Write-Host "Permissions set successfully." -ForegroundColor Green
    } else {
        Write-Host "Build failed with errors." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Error running PyInstaller: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Read-Host "Press Enter to continue..."
