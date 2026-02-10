# Mossy Manager - Mod Merging Guide

## Overview

Mossy Manager is an advanced mod merging tool for Bethesda games (Fallout 4, Skyrim SE, etc.) that helps reduce the number of BA2 archive files by intelligently merging compatible mods together.

## Why Merge Mods?

Merging mods provides several benefits:

1. **Performance**: Fewer BA2 files = faster game loading and better performance
2. **Simplified Load Order**: Easier to manage asset priorities
3. **Memory Efficiency**: Reduces file handles in the operating system
4. **Conflict Resolution**: Allows deliberate layering of conflicting assets

## Understanding BA2 Archives

BA2 (Bethesda Archive 2) files are compressed archives containing game assets:

- **GENERAL archives**: Contain meshes, scripts, sounds, and other general files
- **DDS archives**: Contain textures (DDS format)

Each mod can have multiple BA2 archives, and Mossy Manager can merge compatible archives to reduce the total count.

## Installation

```bash
npm install
npm run build
```

## Usage

### 1. Scan Mods

Scan a directory to see what mods are available:

```bash
npm start -- scan /path/to/mods
```

This will show:
- Mod names
- Number of archives
- Archive types (GENERAL or DDS)
- File sizes
- Plugin files (ESP/ESM/ESL)

### 2. Check Compatibility

Check which mods can be safely merged:

```bash
npm start -- check /path/to/mods
```

This analyzes:
- File conflicts between mods
- Plugin conflicts
- Archive type compatibility
- Suggested merge groups

### 3. Merge Mods

Execute the merge operation:

```bash
npm start -- merge /path/to/mods
```

Options:
- `-o, --output <path>`: Output directory (default: ./merged)
- `--no-backup`: Skip creating backups
- `--overwrite`: Overwrite existing merged archives
- `--validate`: Validate merged archives after creation

Example with options:
```bash
npm start -- merge /path/to/mods -o /path/to/output --validate
```

## Merge Safety Rules

Mossy Manager follows strict safety rules:

### ✅ Safe to Merge

- Mods with different content (no file conflicts)
- Texture packs from the same author
- Mods with compatible archive types
- Non-conflicting plugins

### ⚠️ Risky/Avoided

- Mods with plugin conflicts (same ESP/ESM names)
- High number of file conflicts
- Mods with different texture quality levels
- Script-heavy mods

## How Merging Works

1. **Scan**: Parse all mod directories and read BA2 metadata
2. **Analyze**: Detect conflicts and incompatibilities
3. **Plan**: Group compatible mods by type and compatibility
4. **Execute**: Merge BA2 archives while preserving structure
5. **Validate**: Verify merged archives are valid

## Merge Groups

Mossy Manager creates merge groups based on:

- **Archive Type**: GENERAL and DDS archives are grouped separately
- **Compatibility**: Only conflict-free mods are grouped together
- **Optimization**: Maximizes the number of mods per group

## Best Practices

1. **Always backup**: Keep original mod archives before merging
2. **Test in-game**: After merging, test your game for stability
3. **Document merges**: Keep track of which mods were merged
4. **Incremental merging**: Start with small groups, then expand
5. **Monitor conflicts**: Check the compatibility report carefully

## Technical Details

### File Structure After Merge

Merged archives maintain:
- Original file paths
- Compression settings
- Archive type (GENERAL or DDS)

### Conflict Resolution

When conflicts are detected:
- **Low conflicts** (< 5 files): Warning issued, merge allowed
- **Medium conflicts** (5-20 files): Strong warning, merge allowed
- **High conflicts** (> 20 files): Merge blocked

### Output Files

Merged archives are named:
```
MossyMerge_<Type>_<Count>mods.ba2
```

Example: `MossyMerge_Textures_5mods.ba2`

## Troubleshooting

### "No compatible merge groups found"

This means:
- Mods have conflicting files
- Mods have the same plugins
- Less than 2 compatible mods exist

Solution: Review individual mod conflicts with the `check` command

### "Merge operation failed"

Possible causes:
- Insufficient disk space
- Permission issues
- Corrupted source archives

Solution: Check disk space and file permissions

### Game Crashes After Merge

If the game crashes after merging:
1. Restore from backup
2. Review conflict warnings
3. Merge smaller groups
4. Test each merge separately

## Advanced Usage

### Custom Merge Groups

For manual control, you can:
1. Use `check` to identify compatible mods
2. Create separate directories for each merge group
3. Run `merge` on each directory individually

### Integration with Mod Organizer 2

Mossy Manager can scan MO2's mod directory:
```bash
npm start -- scan "C:\Games\MO2\mods"
```

## Current Limitations

This implementation provides:
- ✅ Mod scanning and metadata extraction
- ✅ Conflict detection
- ✅ Compatibility analysis
- ✅ Merge planning and grouping
- ✅ CLI interface

For production use, you would need:
- Full BA2 binary format implementation
- Archive compression/decompression
- Proper offset calculation in merged archives
- Integration with tools like Cathedral Asset Optimizer

## Technical Implementation Notes

The current implementation is a **framework** that demonstrates the complete workflow for mod merging. The BA2 file format handling is simplified and would require integration with existing tools or implementation of the full binary format specification for production use.

For actual BA2 manipulation, consider integrating:
- Cathedral Asset Optimizer (CAO)
- BSArch
- BA2 Tools

## Support

For issues or questions:
- Review the conflict detection output
- Check merge warnings
- Consult Bethesda modding communities
- Always maintain backups

## License

See LICENSE file for details.
