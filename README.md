# Mossy Manager
A Mod Organizer 2 (MO2) Manager Application

## Description

Mossy Manager is a user-friendly application designed to help manage your Mod Organizer 2 installations. It provides a convenient interface for managing mods, launching MO2, and configuring your modding environment.

## Features

- 🎮 **Easy MO2 Path Management** - Quickly set and manage your MO2 installation location
- 📋 **Mod List Viewer** - View all installed mods in your MO2 installation
- 🚀 **Quick Launch** - Launch Mod Organizer 2 directly from the application
- ⚙️ **Customizable Settings** - Configure application preferences
- 🖥️ **User-Friendly Interface** - Clean, intuitive GUI built with tkinter

## Requirements

- Python 3.8 or higher (for running from source)
- Mod Organizer 2 installation (the application manages MO2, doesn't replace it)

## Installation

### Option 1: Using the Pre-built Executable (Recommended)

1. Download the latest release from the [Releases](https://github.com/POINTYTHRUNDRA654/Mossy-manager./releases) page
2. Extract the executable to your desired location
3. Run `MossyManager.exe` (Windows) or `MossyManager` (Linux/Mac)

### Option 2: Running from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/POINTYTHRUNDRA654/Mossy-manager.git
   cd Mossy-manager
   ```

2. Install dependencies (optional, only needed for building):
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python3 mossy_manager.py
   ```

## Building the Executable

You can create your own standalone executable using the provided build scripts.

### Windows

1. Install Python 3.8+ and ensure it's in your PATH
2. Run the build script:
   ```batch
   build.bat
   ```
3. The executable will be created in the `dist` folder as `MossyManager.exe`

### Linux/Mac

1. Install Python 3.8+ if not already installed
2. Run the build script:
   ```bash
   ./build.sh
   ```
3. The executable will be created in the `dist` folder as `MossyManager`

### Manual Build

If you prefer to build manually:

```bash
# Install PyInstaller
pip install pyinstaller

# Build using the spec file
pyinstaller mossy_manager.spec

# Or build with default settings
pyinstaller --onefile --windowed --name MossyManager mossy_manager.py
```

## Usage

1. **Launch the Application**
   - Run the executable or `python3 mossy_manager.py`

2. **Set MO2 Path**
   - In the Manager tab, click "Browse..." to select your Mod Organizer 2 installation directory
   - This should be the folder containing `ModOrganizer.exe`

3. **View Mods**
   - Once the path is set, click "Refresh Mods" to see your installed mods
   - The list will display all mod folders found in your MO2/mods directory

4. **Launch MO2**
   - Click "Launch MO2" to start Mod Organizer 2 directly from the application

5. **Configure Settings**
   - Visit the Settings tab to customize the application behavior
   - Save your preferences using the "Save Settings" button

## Testing

### Automated Tests

Run the comprehensive test suite:

```bash
python3 test_mossy_manager.py
```

The test suite includes:
- Settings management tests
- Path validation tests
- Mod discovery tests
- Cross-platform compatibility tests
- Configuration file operations tests

All tests run without requiring a GUI or display.

### Demo Mode

Try the interactive demo to see how the application works:

```bash
python3 demo.py
```

This creates a test MO2 structure and demonstrates core functionality.

### Manual Testing

See [TESTING.md](TESTING.md) for comprehensive manual testing instructions.

## Usage

1. **Launch the Application**
   - Run the executable or `python3 mossy_manager.py`

2. **Set MO2 Path**
   - In the Manager tab, click "Browse..." to select your Mod Organizer 2 installation directory
   - This should be the folder containing `ModOrganizer.exe`

3. **View Mods**
   - Once the path is set, click "Refresh Mods" to see your installed mods
   - The list will display all mod folders found in your MO2/mods directory

4. **Launch MO2**
   - Click "Launch MO2" to start Mod Organizer 2 directly from the application

5. **Configure Settings**
   - Visit the Settings tab to customize the application behavior
   - Save your preferences using the "Save Settings" button

## File Structure

```
Mossy-manager/
├── mossy_manager.py      # Main application source code
├── mossy_manager.spec    # PyInstaller specification file
├── requirements.txt      # Python dependencies
├── build.sh             # Linux/Mac build script
├── build.bat            # Windows build script
├── test_mossy_manager.py # Automated test suite
├── demo.py              # Demo and testing script
├── README.md            # This file
├── TESTING.md           # Comprehensive testing guide
├── QUICKSTART.md        # Quick start guide
├── RELEASING.md         # Release instructions
└── LICENSE              # GPL-3.0 License
```

## Troubleshooting

### The executable won't run
- **Windows**: Make sure you have the Visual C++ Redistributable installed
- **Linux**: Ensure the executable has execute permissions: `chmod +x MossyManager`
- Try running from source to see detailed error messages

### Can't find MO2 mods
- Verify that you've selected the correct MO2 installation directory
- The path should contain a `mods` subfolder
- Make sure MO2 is properly installed

### Build fails
- Ensure Python 3.8+ is installed and in your PATH
- Try installing PyInstaller manually: `pip install pyinstaller`
- Check that you have write permissions in the directory

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built for the modding community
- Designed to work with [Mod Organizer 2](https://github.com/ModOrganizer2/modorganizer)

## Support

If you encounter any issues or have questions:
1. Check the [Issues](https://github.com/POINTYTHRUNDRA654/Mossy-manager./issues) page
2. Create a new issue with details about your problem
3. Include your OS, Python version, and error messages if applicable
