# Mossy Manager

Advanced mod merging tool for Bethesda games (Fallout 4, Skyrim SE, etc.)

## Overview

Mossy Manager intelligently merges compatible mod BA2 archives together, reducing the number of archive files and improving game performance. The tool analyzes mod compatibility, detects conflicts, and creates optimized merge groups.

## Features

- 🔍 **Smart Mod Scanning**: Automatically detect and analyze mods
- ⚡ **Conflict Detection**: Identify file and plugin conflicts
- 🎯 **Intelligent Grouping**: Create optimal merge groups by compatibility
- 🛡️ **Safe Merging**: Built-in validation and backup system
- 📊 **Detailed Analysis**: View compatibility reports and merge suggestions
- 💻 **CLI Interface**: Easy-to-use command-line tools

## Why Merge Mods?

Merging BA2 archives provides several benefits:

1. **Better Performance**: Fewer files = faster loading times
2. **Simplified Management**: Easier load order organization  
3. **Memory Efficiency**: Reduced file handle overhead
4. **Conflict Resolution**: Deliberate asset layering

## Installation

```bash
npm install
npm run build
```

## Quick Start

### Scan your mods

```bash
npm start -- scan /path/to/mods
```

### Check merge compatibility

```bash
npm start -- check /path/to/mods
```

### Merge compatible mods

```bash
npm start -- merge /path/to/mods -o ./merged --validate
```

### Auto-detect mod managers

```bash
npm start -- detect
```

## Commands

### `scan`
Display information about mods in a directory

```bash
npm start -- scan <directory>
```

**Features:**
- Colorized output for better readability
- Archive type identification (GENERAL/DDS)
- Plugin detection (ESP/ESM/ESL)
- Size information

### `check`
Analyze merge compatibility and show suggested groups

```bash
npm start -- check <directory>
```

**Features:**
- Smart grouping by archive type
- Conflict detection
- Merge recommendations
- Impact analysis (reduction percentage)

### `merge`
Execute mod merging operations

```bash
npm start -- merge <directory> [options]

Options:
  -o, --output <path>  Output directory (default: ./merged)
  --no-backup          Skip creating backups
  --overwrite          Overwrite existing merged archives
  --validate           Validate merged archives
  --dry-run            Preview merge without executing
  -y, --yes            Skip confirmation prompts
```

**Features:**
- Dry-run mode for safe preview
- Interactive confirmation
- Detailed merge plan display
- Progress indicators
- Comprehensive error handling

### `detect`
Auto-detect installed mod managers

```bash
npm start -- detect
```

**Features:**
- Detects Mod Organizer 2 (MO2)
- Detects Vortex
- Shows game installation paths
- Provides quick-start commands

### `config`
View or update configuration

```bash
# Show current config
npm start -- config --show

# Set default output directory
npm start -- config --set-output /path/to/output

# Enable/disable backups by default
npm start -- config --enable-backup
npm start -- config --disable-backup
```

**Features:**
- Persistent configuration
- Default settings for common options
- Stores last used directory

## How It Works

1. **Scan**: Parse mod directories and BA2 archives
2. **Analyze**: Detect conflicts and check compatibility
3. **Plan**: Group compatible mods by type and compatibility
4. **Merge**: Combine BA2 archives while preserving structure
5. **Validate**: Verify merged archives are correct

## Safety Features

- ✅ Conflict detection (file and plugin level)
- ✅ Archive type compatibility checking
- ✅ Automatic backup creation
- ✅ Post-merge validation
- ✅ Detailed error reporting

## Merge Rules

**Safe to merge:**
- Mods with no file conflicts
- Compatible archive types (GENERAL with GENERAL, DDS with DDS)
- No plugin conflicts (ESP/ESM/ESL)
- Low conflict severity

**Avoided:**
- High file conflicts (20+ files)
- Plugin name conflicts  
- Mixed archive types
- Incompatible mod categories

## Documentation

- [Merge Guide](docs/MERGE_GUIDE.md) - Detailed usage instructions
- [Architecture](docs/ARCHITECTURE.md) - Technical design documentation

## Technical Details

Built with TypeScript and Node.js, Mossy Manager provides:
- Complete mod analysis workflow
- Intelligent compatibility detection
- Safe merge execution framework

**Note**: This implementation provides the complete business logic and workflow for mod merging. For production use with real BA2 archives, integration with existing BA2 manipulation tools (like Cathedral Asset Optimizer or BSArch) would be needed for binary format handling.

## Development

```bash
# Install dependencies
npm install

# Build
npm run build

# Run CLI
npm start -- <command>
```

## License

See [LICENSE](LICENSE) file for details.

## Contributing

Contributions welcome! Please ensure:
- Code follows TypeScript best practices
- Changes maintain type safety
- Documentation is updated
- Safety features are preserved

## Support

For questions or issues:
- Check the documentation in `/docs`
- Review compatibility warnings carefully
- Always maintain backups before merging
- Test merged archives in-game

---

**⚠️ Important**: Always backup your mods before merging! Test merged archives in-game to ensure compatibility.
