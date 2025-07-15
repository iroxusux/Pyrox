# PowerShell Build Script for Pyrox
# This script sets up the development environment and installs dependencies

param(
    [switch]$Clean = $false,
    [switch]$Verbose = $false
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Change to script directory
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host "=== Pyrox Build Script ===" -ForegroundColor Green
Write-Host "Starting build process..." -ForegroundColor Yellow

# Check if Python is available
try {
    $pythonVersion = python --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Host "✓ $pythonVersion detected" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check Python version (requires 3.13+)
try {
    python -c "import sys; exit(0 if sys.version_info >= (3, 13) else 1)" 2>$null
    if ($LASTEXITCODE -ne 0) {
        $currentVersion = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        Write-Host "Error: Python 3.13 or higher is required. Found: $currentVersion" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Error: Could not verify Python version" -ForegroundColor Red
    exit 1
}

# Clean virtual environment if requested
if ($Clean -and (Test-Path ".venv")) {
    Write-Host "Cleaning existing virtual environment..." -ForegroundColor Yellow
    Remove-Item ".venv" -Recurse -Force
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "✓ Virtual environment exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".venv\Scripts\Activate.ps1"

# Verify activation
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Error: Failed to activate virtual environment" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Virtual environment activated: $env:VIRTUAL_ENV" -ForegroundColor Green

# Upgrade pip first
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "Warning: Failed to upgrade pip" -ForegroundColor Yellow
}

# Install/upgrade requirements
if (Test-Path "requirements.txt") {
    Write-Host "Installing requirements from requirements.txt..." -ForegroundColor Yellow
    $pipArgs = @("-r", "requirements.txt", "--upgrade")
    if (-not $Verbose) {
        $pipArgs += "--quiet"
    }
    python -m pip install @pipArgs
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Requirements installed" -ForegroundColor Green
    } else {
        Write-Host "Error: Failed to install requirements" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Warning: requirements.txt not found" -ForegroundColor Yellow
}

# Install the package in development mode
Write-Host "Installing Pyrox package in development mode..." -ForegroundColor Yellow
if (Test-Path "pyproject.toml") {
    $pipArgs = @("-e", ".", "--upgrade")
    if (-not $Verbose) {
        $pipArgs += "--quiet"
    }
    python -m pip install @pipArgs
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Pyrox package installed in development mode" -ForegroundColor Green
    } else {
        Write-Host "Error: Failed to install Pyrox package" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Warning: pyproject.toml not found, skipping package installation" -ForegroundColor Yellow
}

# Verify installation
Write-Host "Verifying installation..." -ForegroundColor Yellow
try {
    $importTest = python -c "import pyrox; print('✓ Pyrox module imported successfully')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host $importTest -ForegroundColor Green
    } else {
        Write-Host "Warning: Could not import pyrox module" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Warning: Could not verify pyrox import" -ForegroundColor Yellow
}

# Show build summary
Write-Host ""
Write-Host "=== Build Summary ===" -ForegroundColor Cyan
$pythonVersionFull = python -c "import sys; print(sys.version.split()[0])"
Write-Host "Python version: $pythonVersionFull" -ForegroundColor White
Write-Host "Virtual environment: $env:VIRTUAL_ENV" -ForegroundColor White

if ($Verbose) {
    Write-Host "Installed packages:" -ForegroundColor White
    python -m pip list --format=columns | Select-Object -First 20 | Write-Host
}

Write-Host ""
Write-Host "✓ Build process completed successfully!" -ForegroundColor Green
Write-Host "You can now run the deployment script with: .\deploy.ps1" -ForegroundColor Cyan
