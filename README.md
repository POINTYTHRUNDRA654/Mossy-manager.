# Mossy Manager

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**Mossy Manager** is a comprehensive command-line tool for managing Mod Organizer 2 (MO2) installations. It provides powerful features for load order management, conflict resolution, and patch creation to help you maintain a stable and optimized modded game setup.

## Features

### 🎯 Load Order Management
- **List and View**: Display your current plugin load order with detailed statistics
- **Validate**: Check for load order issues (e.g., masters loading after regular plugins)
- **Optimize**: Automatically sort plugins by type (masters first, then light plugins, then regular)
- **Enable/Disable**: Manage which plugins are active

### 🔍 Conflict Resolution
- **Scan**: Detect file conflicts between mods
- **Analyze**: Identify which files are overridden and by which mods
- **Severity Rating**: Classify conflicts by severity (Critical, High, Medium, Low)
- **Reports**: Generate detailed conflict reports for review

### 🔧 Patching System
- **Create**: Build custom compatibility patches
- **Apply**: Apply patches to mods with validation
- **Dry Run**: Test patches without making changes
- **Merge**: Combine conflicting files intelligently

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/POINTYTHRUNDRA654/Mossy-manager.
cd Mossy-manager.

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Using pip (once published)

```bash
pip install mossy-manager
```

## Quick Start

### 1. View Your Load Order

```bash
mossy loadorder list --plugins-file "C:\Users\YourName\AppData\Local\ModOrganizer\profiles\Default\plugins.txt"
```

### 2. Validate Load Order

```bash
mossy loadorder validate --plugins-file "path/to/plugins.txt"
```

### 3. Optimize Load Order

```bash
mossy loadorder optimize --plugins-file "path/to/plugins.txt" --output "optimized_loadorder.txt"
```

### 4. Scan for Conflicts

```bash
mossy conflicts scan --mods-dir "C:\Modding\ModOrganizer2\mods"
```

### 5. Create a Compatibility Patch

```bash
mossy patch create --name "MyCompatibilityPatch" --description "Fixes conflicts between ModA and ModB"
```

### 6. Apply a Patch

```bash
mossy patch apply --patch-file "patches/MyCompatibilityPatch.json" --mod-dir "path/to/mod"
```

## Usage

### Load Order Commands

```bash
# List all plugins with their status
mossy loadorder list --plugins-file plugins.txt

# Validate load order for issues
mossy loadorder validate --plugins-file plugins.txt

# Optimize load order automatically
mossy loadorder optimize --plugins-file plugins.txt --output optimized.txt
```

### Conflict Resolution Commands

```bash
# Scan mods directory for conflicts
mossy conflicts scan --mods-dir "path/to/mods" --output conflict_report.txt
```

### Patching Commands

```bash
# Create a new patch
mossy patch create --name "PatchName" --description "What this patch does"

# List all available patches
mossy patch list --patches-dir "./patches"

# Apply a patch (with dry run first)
mossy patch apply --patch-file "patch.json" --mod-dir "path/to/mod" --dry-run

# Apply patch for real
mossy patch apply --patch-file "patch.json" --mod-dir "path/to/mod"
```

### General Commands

```bash
# Display help
mossy --help

# Display version
mossy --version

# Display detailed information
mossy info

# Enable verbose logging
mossy --verbose loadorder list --plugins-file plugins.txt
```

## File Formats

### plugins.txt
Standard MO2 format:
```
# Comment line
*Skyrim.esm
*Update.esm
*Dawnguard.esm
SomeMod.esp
*AnotherMod.esp
```
- Lines starting with `*` indicate enabled plugins
- Lines without `*` are disabled plugins

### loadorder.txt
Simple list format:
```
# Load order file
Skyrim.esm
Update.esm
Dawnguard.esm
SomeMod.esp
AnotherMod.esp
```

### Patch Files
JSON format for defining patch operations:
```json
{
  "name": "MyPatch",
  "description": "Compatibility patch for ModA and ModB",
  "created_at": "2026-02-09T00:00:00",
  "operations": [
    {
      "type": "replace",
      "file": "Data/config.ini",
      "content": "new content here"
    },
    {
      "type": "merge",
      "file": "Data/scripts/init.psc",
      "content": "additional script content"
    }
  ],
  "target_mods": ["ModA", "ModB"]
}
```

## Understanding Conflict Severity

- **Critical**: Plugin files (.esp, .esm, .esl) - Only one mod should provide each plugin
- **High**: Scripts (.pex, .psc) - May cause gameplay issues if incompatible
- **Medium**: Resources (textures, meshes, sounds) - Last mod in load order wins
- **Low**: Configuration and text files - Usually safe to override

## Examples

### Example 1: Complete Load Order Management

```bash
# Step 1: Check current load order
mossy loadorder list --plugins-file plugins.txt

# Step 2: Validate for issues
mossy loadorder validate --plugins-file plugins.txt

# Step 3: Optimize if needed
mossy loadorder optimize --plugins-file plugins.txt --output new_loadorder.txt
```

### Example 2: Resolving Mod Conflicts

```bash
# Step 1: Scan for conflicts
mossy conflicts scan --mods-dir "C:\Games\ModOrganizer2\mods" --output conflicts.txt

# Step 2: Review the report
cat conflicts.txt

# Step 3: Create a compatibility patch if needed
mossy patch create --name "ModA_ModB_Compat" --description "Resolves texture conflicts"
```

### Example 3: Creating and Testing a Patch

```bash
# Create the patch
mossy patch create --name "TestPatch" --description "Test compatibility patch"

# Edit the patch file (patches/TestPatch.json) to add operations

# Test with dry run
mossy patch apply --patch-file patches/TestPatch.json --mod-dir "path/to/mod" --dry-run

# Apply if everything looks good
mossy patch apply --patch-file patches/TestPatch.json --mod-dir "path/to/mod"
```

## Architecture

```
mossy_manager/
├── core/
│   ├── load_order.py      # Load order management
│   ├── conflict_resolver.py  # Conflict detection and resolution
│   └── patcher.py         # Patch creation and application
├── cli/
│   └── main.py            # Command-line interface
└── utils/
    └── (utility functions)
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

This project follows PEP 8 style guidelines.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Designed for use with [Mod Organizer 2](https://www.modorganizer.org/)
- Inspired by the modding communities of Bethesda games

## Support

For issues, questions, or suggestions, please open an issue on the [GitHub repository](https://github.com/POINTYTHRUNDRA654/Mossy-manager./issues).

## Roadmap

- [ ] GUI interface using PyQt6
- [ ] Automatic mod compatibility detection
- [ ] Integration with Nexus Mods API
- [ ] Backup and restore functionality
- [ ] Profile management
- [ ] Plugin cleaning and optimization
- [ ] Advanced dependency resolution

---

**Made with ❤️ for the modding community**
