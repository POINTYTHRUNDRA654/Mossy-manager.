#!/bin/bash
# Build script for creating Mossy Manager executable

echo "Building Mossy Manager executable..."
echo "===================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" &> /dev/null; then
    echo "Installing PyInstaller..."
    pip install -r requirements.txt
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Build the executable
echo "Building executable..."
pyinstaller mossy_manager.spec

# Check if build was successful
if [ -f "dist/MossyManager" ] || [ -f "dist/MossyManager.exe" ]; then
    echo ""
    echo "===================================="
    echo "Build successful!"
    echo "Executable location: dist/MossyManager"
    echo "===================================="
else
    echo ""
    echo "===================================="
    echo "Build failed! Check the output above for errors."
    echo "===================================="
    exit 1
fi
