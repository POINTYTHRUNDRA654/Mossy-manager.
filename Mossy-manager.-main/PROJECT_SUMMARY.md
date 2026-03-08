# Mossy Manager - Project Summary

## Overview

**Mossy Manager** is a comprehensive command-line tool for managing Mod Organizer 2 (MO2) installations. It addresses the three core requirements specified:

1. ✅ **Load Order Management**
2. ✅ **Conflict Resolution**
3. ✅ **Patching System**

## Implementation Details

### Architecture

```
Python 3.8+ Application
├── Core Modules (Business Logic)
│   ├── load_order.py - Plugin load order management
│   ├── conflict_resolver.py - Conflict detection and analysis
│   └── patcher.py - Patch creation and application
├── CLI Interface (User Interaction)
│   └── main.py - Command-line interface with Click
└── Tests (Quality Assurance)
    ├── test_load_order.py
    ├── test_conflict_resolver.py
    └── test_patcher.py
```

### Core Features

#### 1. Load Order Management (`load_order.py`)

**Capabilities:**
- Read/write MO2 plugins.txt and loadorder.txt files
- Enable/disable individual plugins
- Automatic optimization (sorts plugins by type: masters → light → regular)
- Validation to detect common issues
- Statistical analysis and reporting

**Key Classes:**
- `Plugin` - Represents a mod plugin with metadata
- `LoadOrderManager` - Manages plugin collections and load order

**CLI Commands:**
```bash
mossy loadorder list        # Display current load order
mossy loadorder validate    # Check for issues
mossy loadorder optimize    # Auto-sort plugins
```

#### 2. Conflict Resolution (`conflict_resolver.py`)

**Capabilities:**
- Scan mod directories for file conflicts
- Classify conflicts by severity:
  - **Critical**: Plugin files (.esp, .esm, .esl)
  - **High**: Scripts (.pex, .psc)
  - **Medium**: Resources (textures, meshes, sounds)
  - **Low**: Configuration and text files
- Analyze conflicts with load order context
- Determine "winners" based on load order
- Generate detailed reports with suggestions

**Key Classes:**
- `Conflict` - Represents a single conflict
- `ConflictType` - Enum for conflict types
- `ConflictResolver` - Scans and analyzes conflicts

**CLI Commands:**
```bash
mossy conflicts scan --mods-dir path/to/mods
```

#### 3. Patching System (`patcher.py`)

**Capabilities:**
- Create custom patches in JSON format
- Support multiple operation types:
  - **replace**: Replace file content
  - **add**: Add new files
  - **delete**: Remove files
  - **merge**: Append to existing files
- Save/load patches from disk
- Validate patches before application
- Dry-run mode for safe testing
- Create compatibility patches automatically

**Key Classes:**
- `Patch` - Represents a patch with operations
- `Patcher` - Manages patch creation and application

**CLI Commands:**
```bash
mossy patch create --name "PatchName"
mossy patch list
mossy patch apply --patch-file patch.json --mod-dir path
```

### Technology Stack

- **Language**: Python 3.8+
- **CLI Framework**: Click (command-line interface)
- **Output Formatting**: 
  - Colorama (colored terminal output)
  - Tabulate (table formatting)
- **Data Formats**: 
  - Text files (plugins.txt, loadorder.txt)
  - JSON (patches)
- **Testing**: pytest with 38 comprehensive tests

### Quality Metrics

✅ **Test Coverage**: 38/38 tests passing
✅ **Code Review**: No issues found
✅ **Security Scan**: No vulnerabilities detected (CodeQL)
✅ **Code Style**: PEP 8 compliant
✅ **Documentation**: Comprehensive (README, EXAMPLES, CONTRIBUTING)

## Usage Examples

### Basic Workflow

```bash
# 1. Check current load order
mossy loadorder list --plugins-file plugins.txt

# 2. Validate for issues
mossy loadorder validate --plugins-file plugins.txt

# 3. Optimize if needed
mossy loadorder optimize --plugins-file plugins.txt --output optimized.txt

# 4. Scan for conflicts
mossy conflicts scan --mods-dir /path/to/mods --output report.txt

# 5. Create compatibility patch if needed
mossy patch create --name "Compat_ModA_ModB"

# 6. Apply patch
mossy patch apply --patch-file patch.json --mod-dir /path/to/mod
```

### Real-World Example

```bash
# Windows MO2 installation
mossy loadorder list \
  --plugins-file "C:\Users\Name\AppData\Local\ModOrganizer\profiles\Default\plugins.txt"

mossy conflicts scan \
  --mods-dir "C:\Modding\ModOrganizer2\mods" \
  --output conflicts.txt

mossy patch create \
  --name "SMIM_ENB_Compat" \
  --description "Compatibility between SMIM and ENB"
```

## File Formats

### plugins.txt (MO2 Standard)
```
# Comment
*Skyrim.esm       # Enabled (prefix with *)
*Update.esm
SomeMod.esp      # Disabled (no prefix)
```

### loadorder.txt (MO2 Standard)
```
# Load order (priority 1-255)
Skyrim.esm
Update.esm
SomeMod.esp
```

### Patch File (JSON)
```json
{
  "name": "CompatPatch",
  "description": "Fixes conflicts",
  "operations": [
    {
      "type": "replace",
      "file": "config.ini",
      "content": "new content"
    }
  ],
  "target_mods": ["ModA", "ModB"]
}
```

## Installation

```bash
# Clone repository
git clone https://github.com/POINTYTHRUNDRA654/Mossy-manager.
cd Mossy-manager.

# Install dependencies
pip install -r requirements.txt

# Install package
pip install -e .

# Verify installation
mossy --version
mossy info
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=mossy_manager --cov-report=html

# All 38 tests pass successfully
```

## Project Statistics

- **Lines of Code**: ~2,500+ (excluding tests)
- **Test Files**: 3 (38 test cases)
- **Core Modules**: 3 (load_order, conflict_resolver, patcher)
- **CLI Commands**: 11 (across 3 command groups)
- **Documentation**: 3 files (README, EXAMPLES, CONTRIBUTING)
- **Example Files**: Included (demo directory)

## Future Enhancements

Potential additions (not currently implemented):
- GUI interface using PyQt6
- Integration with Nexus Mods API
- Automatic mod compatibility detection
- Backup and restore functionality
- Profile management
- Plugin cleaning and optimization
- Advanced dependency resolution
- Database support for large mod collections
- Conflict resolution automation
- Batch operations

## Compliance & Security

✅ **MIT License** - Open source and permissive
✅ **No Security Vulnerabilities** - Verified with CodeQL
✅ **No External API Dependencies** - Works offline
✅ **Safe File Operations** - Validates paths and permissions
✅ **Dry-Run Support** - Test before applying changes

## Conclusion

Mossy Manager successfully implements all three requested features for Mod Organizer 2:

1. **Load Order Management** - Full support for reading, validating, and optimizing plugin load orders
2. **Conflict Resolution** - Comprehensive conflict detection with severity classification and reporting
3. **Patching** - Flexible patching system with multiple operations and validation

The application is production-ready with:
- Clean, modular architecture
- Comprehensive test coverage
- Full documentation
- Security validation
- User-friendly CLI interface

Ready for use with Mod Organizer 2 installations!
