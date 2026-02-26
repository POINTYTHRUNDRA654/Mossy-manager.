# Mossy Manager

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![GitHub release](https://img.shields.io/github/v/release/POINTYTHRUNDRA654/Mossy-manager.)](https://github.com/POINTYTHRUNDRA654/Mossy-manager./releases/latest)

**Mossy Manager** is a comprehensive tool for managing Mod Organizer 2 (MO2) installations, with **advanced Fallout 4 support**. It provides powerful features for load order management, conflict resolution, and patch creation to help you maintain a stable and optimized modded game setup.

## 🚀 Quick Start

**Want to get started right away?**

1. 📥 **[Download MossyManager.exe](https://github.com/POINTYTHRUNDRA654/Mossy-manager./releases/tag/latest)** - Always-current build, no Python needed!
2. 📖 **[Read the Quick Start Guide](QUICKSTART.md)** - Get up and running in 5 minutes
3. 🎮 **Run**: `MossyManager.exe auto --profile "Default"` - Optimize your Fallout 4 setup automatically!

**Need help downloading?** See [HOW_TO_DOWNLOAD.md](HOW_TO_DOWNLOAD.md) for detailed instructions.

## 🎮 Using Mossy Manager inside Mod Organizer 2

Mossy Manager can be launched directly from MO2 so it runs through MO2's virtual
file system (giving it access to your active mods and profile).

### Step-by-step setup

1. **Download** `MossyManager.exe` from the
   [latest release](https://github.com/POINTYTHRUNDRA654/Mossy-manager./releases/tag/latest).
2. **Save** it somewhere permanent, e.g. your MO2 `tools\MossyManager\` folder.
3. Open **Mod Organizer 2**.
4. Click the **gear icon** (⚙) in the MO2 toolbar → **Executables**.
5. Click the **+** button to add a new executable and fill in:

   | Field | Value |
   |-------|-------|
   | Title | `Mossy Manager` |
   | Binary | `C:\...\MossyManager.exe` *(browse to where you saved it)* |
   | Arguments | `auto --profile "Default"` *(replace `Default` with your profile name)* |
   | Start in | *(leave blank — Mossy Manager auto-detects MO2)* |

6. Click **OK** and close the Executables dialog.
7. Select **Mossy Manager** from the executable dropdown next to the **Run** button
   and click **Run**.

Mossy Manager will auto-detect your MO2 installation, optimize your load order,
scan for conflicts, and print a full report — all without leaving MO2.

## 🌟 NEW: Fallout 4 Advanced Integration

Mossy Manager now includes **comprehensive Fallout 4 knowledge** and can automatically optimize your load order for maximum stability!

- **Advanced Load Order Rules**: Uses expert knowledge of FO4 modding
- **MO2 Integration**: Automatically detects and integrates with Mod Organizer 2
- **One-Click Optimization**: Optimize your entire setup with a single command
- **Automatic Workflow**: Load order → Conflict detection → Recommendations
- **Executable Available**: Download and run without installing Python!

## Features

### 🎯 Load Order Management
- **List and View**: Display your current plugin load order with detailed statistics
- **Validate**: Check for load order issues using game-specific rules
- **Optimize**: Automatically sort plugins using advanced categorization
- **Enable/Disable**: Manage which plugins are active
- **Fallout 4 Expertise**: Special optimization for FO4 with DLC ordering

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

### 🎮 Fallout 4 Specific Features
- **Official DLC Ordering**: Correct order for all Fallout 4 DLCs
- **Plugin Categorization**: 12 categories (Fixes, Frameworks, Weapons, etc.)
- **Dependency Detection**: Automatically detect required DLCs
- **Conflict Groups**: Identify known conflicting mod types
- **Smart Recommendations**: Get suggestions based on your load order

## Installation

### Option 1: Download Executable (Easiest!)

**For Windows users**, download the pre-built executable:

1. Go to [Releases](https://github.com/POINTYTHRUNDRA654/Mossy-manager./releases)
2. Download `MossyManager.exe`
3. Run it directly - no installation needed!

### Option 2: From Source

> ⚠️ **Windows users — important note about the folder name:**
> This repository's name ends with a period (`.`), which Windows does not allow as a
> folder name. If you clone using GitHub Desktop or download the ZIP and get an
> **empty folder**, this is why. Use the workaround below.

#### Windows Workaround (clone via Command Prompt):

```cmd
git clone https://github.com/POINTYTHRUNDRA654/Mossy-manager. MossyManager
cd MossyManager
install.bat
```

The extra `MossyManager` argument tells Git to use a valid Windows folder name.
`install.bat` then installs all dependencies and sets up the tool automatically.

#### Linux / macOS:

```bash
git clone https://github.com/POINTYTHRUNDRA654/Mossy-manager. MossyManager
cd MossyManager
./install.sh
```

#### Manual install (all platforms):

```bash
pip install -r requirements.txt
pip install -e .
```

### Option 3: Build Your Own Executable

```bash
# On Windows
build.bat

# On Linux/Mac
./build.sh
```

### Using pip (once published)

```bash
pip install mossy-manager
```

## Quick Start

### Fallout 4 Users: Automatic Optimization (Recommended!)

The easiest way to optimize your Fallout 4 setup:

```bash
# Let Mossy Manager do everything automatically!
mossy auto --profile "Default"
```

This single command will:
1. Auto-detect your MO2 installation
2. Optimize your load order using FO4 expertise
3. Scan for conflicts
4. Provide recommendations

### Manual Workflow

### 1. Optimize Fallout 4 Load Order

```bash
# Optimizes using advanced FO4 rules
mossy fallout4 optimize --profile "Default"
```

### 2. View Your Load Order

```bash
mossy loadorder list --plugins-file "C:\Users\YourName\AppData\Local\ModOrganizer\profiles\Default\plugins.txt"
```

### 3. Validate Load Order

```bash
mossy loadorder validate --plugins-file "path/to/plugins.txt"
```

### 4. Optimize Load Order (Generic)

```bash
mossy loadorder optimize --plugins-file "path/to/plugins.txt" --output "optimized_loadorder.txt"
```

### 5. Scan for Conflicts

```bash
mossy conflicts scan --mods-dir "C:\Modding\ModOrganizer2\mods"
```

### 6. Create a Compatibility Patch

```bash
mossy patch create --name "MyCompatibilityPatch" --description "Fixes conflicts between ModA and ModB"
```

### 7. Apply a Patch

```bash
mossy patch apply --patch-file "patches/MyCompatibilityPatch.json" --mod-dir "path/to/mod"
```

## Usage

### 🎮 Fallout 4 Commands (NEW!)

```bash
# Automatic workflow - does everything for you!
mossy auto --profile "Default"

# Manual FO4-specific optimization
mossy fallout4 optimize --profile "Default" --mo2-path "C:/MO2"

# Both commands:
# - Auto-detect MO2 installation
# - Create automatic backups
# - Use advanced FO4 knowledge
# - Provide detailed recommendations
```

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

# Create conflict resolution patch using xEdit (add --apply to write exports)
mossy conflicts resolve-xedit --mods-dir "path/to/mods" --xedit-path "path/to/SSEEdit.exe" --apply --auto-launch

# Dry-run summary only (default)
mossy conflicts resolve-xedit --mods-dir "path/to/mods"

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

> Note: `resolve-xedit` runs in dry-run mode by default. Add `--apply` to write exports and scripts. When applying, existing output directories are backed up unless you pass `--no-backup`.

#### Automatic Workflow

```bash
# Scan conflicts and launch xEdit automatically
mossy conflicts resolve-xedit \
  --mods-dir "C:\Modding\ModOrganizer2\mods" \
  --xedit-path "C:\Modding\Tools\SSEEdit\SSEEdit.exe" \
  --patch-name "MyConflictPatch" \
  --apply \
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
  --output-dir "./xedit_output" \
  --apply
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
