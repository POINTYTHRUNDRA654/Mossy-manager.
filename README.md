# Mossy Manager

A powerful command-line tool for managing Mod Organizer 2 (MO2) installations, profiles, and mods.

## Features

- 📦 **Mod Management**: List, enable, disable, and get information about installed mods
- 👤 **Profile Management**: Create, delete, switch between, and list MO2 profiles
- ⚙️ **Configuration Management**: Store and manage your MO2 settings
- 🔍 **Installation Info**: View details about your MO2 setup

## Installation

### Using pip (recommended)

```bash
pip install -e .
```

### Manual Installation

1. Clone the repository:
```bash
git clone https://github.com/POINTYTHRUNDRA654/Mossy-manager..git
cd Mossy-manager.
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install the package:
```bash
pip install -e .
```

## Usage

After installation, you can use the `mossy-manager` command from anywhere in your terminal.

### Mod Management

```bash
# List all mods
mossy-manager mod list --path /path/to/MO2

# Enable a mod
mossy-manager mod enable --name "ModName" --path /path/to/MO2

# Disable a mod
mossy-manager mod disable --name "ModName" --path /path/to/MO2

# Get mod information
mossy-manager mod info --name "ModName" --path /path/to/MO2
```

### Profile Management

```bash
# List all profiles
mossy-manager profile list --path /path/to/MO2

# Create a new profile
mossy-manager profile create --name "MyProfile" --path /path/to/MO2

# Delete a profile
mossy-manager profile delete --name "MyProfile" --path /path/to/MO2

# Switch to a profile
mossy-manager profile switch --name "MyProfile" --path /path/to/MO2
```

### Configuration Management

```bash
# Show all configuration
mossy-manager config show

# Set a configuration value
mossy-manager config set --key mo2_path --value "/path/to/MO2"

# Get a configuration value
mossy-manager config get --key mo2_path
```

### Installation Info

```bash
# Show MO2 installation info
mossy-manager info --path /path/to/MO2
```

## Requirements

- Python 3.6 or higher
- Mod Organizer 2 installation (optional for testing)

## Development

### Running from source

```bash
# Run directly from source
python -m mossy_manager.main --help
```

### Project Structure

```
mossy-manager/
├── mossy_manager/           # Main package
│   ├── __init__.py         # Package initialization
│   ├── main.py             # CLI entry point
│   ├── mod_manager.py      # Mod management logic
│   ├── profile_manager.py  # Profile management logic
│   └── config_manager.py   # Configuration management
├── LICENSE                 # MIT License
├── README.md              # This file
├── requirements.txt       # Python dependencies
└── setup.py              # Package setup file
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

## Acknowledgments

- Mod Organizer 2 team for creating an excellent modding tool
- The modding community for inspiration and support
