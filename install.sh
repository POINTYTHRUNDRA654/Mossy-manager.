#!/bin/bash
# =====================================================================
#  Mossy Manager - Linux/macOS Install Script
#  Run this script after cloning the repository to install from source.
# =====================================================================

set -e

echo "========================================================"
echo " Mossy Manager - Install from Source"
echo "========================================================"
echo

# Check Python installation
if ! command -v python3 &>/dev/null; then
    echo "ERROR: Python 3 not found."
    echo "Please install Python 3.8 or later."
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  macOS:         brew install python"
    exit 1
fi

echo "Python found:"
python3 --version
echo

# Upgrade pip
echo "Upgrading pip..."
python3 -m pip install --upgrade pip
echo

# Install dependencies
echo "Installing dependencies..."
python3 -m pip install -r requirements.txt
echo

# Install Mossy Manager
echo "Installing Mossy Manager..."
python3 -m pip install -e .
echo

echo "========================================================"
echo " Installation complete!"
echo "========================================================"
echo
echo "You can now use Mossy Manager by running:"
echo "  mossy --help"
echo "  mossy auto --profile \"Default\""
echo
echo "To build a standalone executable (no Python required):"
echo "  ./build.sh"
echo
