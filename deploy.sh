#!/bin/bash

# Clean up previous builds
echo "Cleaning up previous builds..."
rm -rf dist/ build/ *.spec

# Stop any running Pyrox processes
pkill -f "Pyrox" 2>/dev/null || true

# Run the build script
source ./build.sh

# Run PyInstaller with improved error handling
echo "Running PyInstaller..."
pyinstaller --name "Pyrox" \
    --noconfirm \
    --noconsole \
    --onedir \
    --icon="pyrox/ui/icons/_def.ico" \
    --add-data "pyrox/ui/icons:pyrox/ui/icons" \
    --add-data "pyrox/tasks:pyrox/tasks" \
    --add-data "pyrox/applications/mod:pyrox/applications/mod" \
    --distpath dist \
    --workpath build \
    --clean \
    __main__.py

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "Build completed successfully!"
    echo "Executable location: dist/Pyrox/Pyrox.exe"
else
    echo "Build failed with errors."
    exit 1
fi

read -p "Press Enter to continue..."