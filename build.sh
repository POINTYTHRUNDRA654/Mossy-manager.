#!/bin/bash
# Build script for Mossy Manager on Linux/Mac

echo "========================================"
echo "Mossy Manager - Build Script"
echo "========================================"
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or later"
    exit 1
fi

echo "Python found:"
python3 --version
echo ""

# Install dependencies
echo "Installing dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install pyinstaller
echo ""

# Run build script
echo "Building executable..."
python3 build.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Build failed! Check errors above."
    exit 1
fi

echo ""
echo "========================================"
echo "Build Complete!"
echo "========================================"
echo ""
echo "The executable is located in: dist/MossyManager"
echo ""
