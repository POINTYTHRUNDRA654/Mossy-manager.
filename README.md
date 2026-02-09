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
- **xEdit Integration**: Export conflicts and create resolution patches using xEdit

### 🔧 Patching System
- **Create**: Build custom compatibility patches
- **Apply**: Apply patches to mods with validation
- **Dry Run**: Test patches without making changes
- **Merge**: Combine conflicting files intelligently
- **xEdit Support**: Generate xEdit scripts for advanced conflict resolution

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

# Create conflict resolution patch using xEdit
mossy conflicts resolve-xedit --mods-dir "path/to/mods" --xedit-path "path/to/SSEEdit.exe" --auto-launch

# Get help for xEdit integration
mossy conflicts xedit-help
```

### Patching Commands

```bash
# Create a new patch
mossy patch create --name "PatchName" --description "What this patch does"

# Create a patch with xEdit integration
mossy patch create-xedit --name "MyPatch" --description "Patch for xEdit" --auto-launch

# Export existing patch to xEdit format
mossy patch export-xedit --patch-file "patch.json" --output-dir "./xedit_patches"

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

## xEdit Integration

Mossy Manager integrates with xEdit (SSEEdit, TES5Edit, FO4Edit, etc.) for advanced conflict resolution and patch creation.

### What is xEdit?

xEdit is a powerful tool for viewing and editing Bethesda game plugins. It allows you to:
- View plugin records in detail
- Detect conflicts between plugins
- Create conflict resolution patches
- Copy records between plugins
- Clean and optimize plugins

### Setting Up xEdit Integration

1. **Download xEdit** for your game from [Nexus Mods](https://www.nexusmods.com/):
   - Skyrim Special Edition: SSEEdit
   - Skyrim: TES5Edit
   - Fallout 4: FO4Edit
   - Fallout 3: FO3Edit
   - Fallout New Vegas: FNVEdit

2. **Extract** xEdit to a known location (e.g., `C:\Modding\Tools\SSEEdit\`)

3. **Get help** with configuration:
   ```bash
   mossy conflicts xedit-help
   ```

### Using xEdit for Conflict Resolution

#### Automatic Workflow

```bash
# Scan conflicts and launch xEdit automatically
mossy conflicts resolve-xedit \
  --mods-dir "C:\Modding\ModOrganizer2\mods" \
  --xedit-path "C:\Modding\Tools\SSEEdit\SSEEdit.exe" \
  --patch-name "MyConflictPatch" \
  --auto-launch
```

This will:
1. Scan all mods for conflicts
2. Export conflicts to JSON format
3. Generate an xEdit Pascal script
4. Launch xEdit with the conflicting plugins
5. Provide instructions for creating the patch

#### Manual Workflow

```bash
# Export conflicts without launching xEdit
mossy conflicts resolve-xedit \
  --mods-dir "C:\Modding\ModOrganizer2\mods" \
  --patch-name "MyConflictPatch" \
  --output-dir "./xedit_output"
```

Then:
1. Open the generated `xedit_output/MyConflictPatch_conflicts.json` to review conflicts
2. Launch xEdit manually
3. Load conflicting plugins
4. Use xEdit's built-in conflict detection
5. Create a new patch plugin
6. Copy conflicting records to your patch
7. Resolve conflicts manually
8. Save and exit xEdit

### Generated Files

When using xEdit integration, Mossy Manager creates:

- **`{PatchName}_conflicts.json`** - Detailed conflict information
- **`{PatchName}_script.pas`** - Pascal script for xEdit to automate patch creation

### Example xEdit Workflow

```bash
# Step 1: Detect conflicts
mossy conflicts scan --mods-dir "C:\Modding\MO2\mods" --output conflicts.txt

# Step 2: Review the conflict report
cat conflicts.txt

# Step 3: Create conflict resolution patch with xEdit
mossy conflicts resolve-xedit \
  --mods-dir "C:\Modding\MO2\mods" \
  --xedit-path "C:\Tools\SSEEdit\SSEEdit.exe" \
  --patch-name "ConflictResolution_Patch" \
  --game skyrimse \
  --auto-launch

# Step 4: In xEdit (automatically opened):
#   - Review detected conflicts
#   - Create new patch plugin
#   - Copy conflicting records
#   - Resolve conflicts
#   - Save and close

# Step 5: Add the patch to your load order
# Place it after all conflicting mods in your load order
```

### Creating Patches with xEdit

Beyond conflict resolution, you can also create general-purpose patches using xEdit:

#### Workflow 1: Create New Patch with xEdit

```bash
# Create a new patch that will be edited in xEdit
mossy patch create-xedit \
  --name "MyGameplayPatch" \
  --description "Custom gameplay modifications" \
  --xedit-path "C:\Tools\SSEEdit\SSEEdit.exe" \
  --target-plugin "MyGameplayPatch.esp" \
  --auto-launch
```

This will:
1. Create a Mossy Manager patch file
2. Generate xEdit-compatible JSON export
3. Create a Pascal script for xEdit
4. Launch xEdit with the new plugin
5. You can then edit records in xEdit
6. Save and use the patch in your load order

#### Workflow 2: Export Existing Patch to xEdit

```bash
# If you have an existing Mossy Manager patch
mossy patch export-xedit \
  --patch-file "patches/MyPatch.json" \
  --xedit-path "C:\Tools\SSEEdit\SSEEdit.exe" \
  --target-plugin "MyPatch.esp" \
  --output-dir "./xedit_patches"
```

This exports the patch operations and generates xEdit scripts for further editing.

#### Generated Files

When creating patches with xEdit, Mossy Manager generates:
- **`{PatchName}_patch.json`** - Structured patch data with operations
- **`{PatchName}_apply.pas`** - Pascal script for xEdit to apply the patch
- **Mossy Manager patch file** - Standard JSON patch file

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
