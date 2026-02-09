# Quick Start Guide - Mossy Manager

## For End Users

### Option 1: Download Pre-built Executable (Easiest)
1. Go to the [Releases](https://github.com/POINTYTHRUNDRA654/Mossy-manager./releases) page
2. Download the latest version for your operating system
3. Run the executable directly (no installation needed!)

### Option 2: Run from Source
If you have Python 3.8+ installed:
```bash
python3 mossy_manager.py
```

## For Developers

### Building Your Own Executable

#### Windows
```batch
# Run the build script
build.bat
```

#### Linux/Mac
```bash
# Make script executable (first time only)
chmod +x build.sh

# Run the build script
./build.sh
```

#### Manual Build
```bash
# Install dependencies
pip install -r requirements.txt

# Build with PyInstaller
pyinstaller mossy_manager.spec
```

The executable will be created in the `dist/` folder.

## Using the Application

1. **Launch** the application
2. **Set MO2 Path**: Click "Browse..." and select your Mod Organizer 2 folder
3. **View Mods**: Click "Refresh Mods" to see all installed mods
4. **Launch MO2**: Click "Launch MO2" to start Mod Organizer 2

## System Requirements

- **Operating System**: Windows 7+, Linux, or macOS
- **For Running from Source**: Python 3.8 or higher
- **For Using Executable**: No additional requirements

## Troubleshooting

### Linux Users
If you get a permission error when running the executable:
```bash
chmod +x MossyManager
./MossyManager
```

### The application won't start
- Try running from source to see detailed error messages
- Check that you have the required system libraries

### Can't find my mods
- Make sure you selected the correct MO2 installation directory
- The folder should contain `ModOrganizer.exe` and a `mods` subfolder

## Need Help?

Visit the [Issues](https://github.com/POINTYTHRUNDRA654/Mossy-manager./issues) page to report problems or ask questions.
