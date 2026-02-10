# Example Usage

This document provides practical examples of using Mossy Manager to merge mods.

## Scenario 1: Simple Texture Mod Merge

You have multiple texture mods that you want to merge together:

```
mods/
├── HD_Textures_Pack_1/
│   └── HDTextures1_Textures.ba2
├── HD_Textures_Pack_2/
│   └── HDTextures2_Textures.ba2
└── HD_Textures_Pack_3/
    └── HDTextures3_Textures.ba2
```

**Step 1: Scan the mods**

```bash
npm start -- scan mods/
```

Output:
```
Found 3 mod(s):

1. HD_Textures_Pack_1
   Archives: 1
     - HDTextures1_Textures.ba2 (DDS, 2.5 GB)
   Plugins: 0

2. HD_Textures_Pack_2
   Archives: 1
     - HDTextures2_Textures.ba2 (DDS, 1.8 GB)
   Plugins: 0

3. HD_Textures_Pack_3
   Archives: 1
     - HDTextures3_Textures.ba2 (DDS, 3.2 GB)
   Plugins: 0
```

**Step 2: Check compatibility**

```bash
npm start -- check mods/
```

Output:
```
Found 1 merge group(s):
  1. Textures Merge (3 mods)
     Output: MossyMerge_Textures_3mods.ba2
     Estimated size: 7.5 GB

Merging would reduce 3 archives to 1 (66.7% reduction)
```

**Step 3: Execute the merge**

```bash
npm start -- merge mods/ -o merged/ --validate
```

Output:
```
Merging mods from: mods/
Output directory: merged/

Planned 1 merge group(s)

Group 1: Textures Merge (3 mods)
  Mods: HD_Textures_Pack_1, HD_Textures_Pack_2, HD_Textures_Pack_3

Executing merges...

✓ Successfully merged 3 mods

=== Summary ===
Successful: 1
Failed: 0
```

## Scenario 2: Mixed Mods with Conflicts

You have mods with potential conflicts:

```
mods/
├── WeaponMeshes/
│   ├── WeaponMeshes.ba2
│   └── WeaponMeshes.esp
├── ArmorMeshes/
│   ├── ArmorMeshes.ba2
│   └── ArmorMeshes.esp
└── CompleteMeshOverhaul/
    ├── CompleteMeshOverhaul.ba2
    └── WeaponMeshes.esp  (CONFLICT!)
```

**Check compatibility:**

```bash
npm start -- check mods/
```

Output:
```
Found 2 merge group(s):
  1. General Merge (2 mods)
     Output: MossyMerge_General_2mods.ba2
     Mods: WeaponMeshes, ArmorMeshes

Note: CompleteMeshOverhaul was not included due to plugin conflict with WeaponMeshes
```

**Result:** Mossy Manager detected the plugin conflict and excluded the conflicting mod from the merge group.

## Scenario 3: Large Mod Collection

You have a large collection with different types:

```
mods/
├── TexturePack_City/
├── TexturePack_Nature/
├── TexturePack_Weapons/
├── MeshImprovement_Buildings/
├── MeshImprovement_Creatures/
├── SoundOverhaul/
└── WeatherEffects/
```

**Check compatibility:**

```bash
npm start -- check mods/
```

Output:
```
Found 3 merge group(s):
  1. Textures Merge (3 mods)
     Mods: TexturePack_City, TexturePack_Nature, TexturePack_Weapons
     Estimated size: 4.2 GB

  2. General Merge (4 mods)
     Mods: MeshImprovement_Buildings, MeshImprovement_Creatures, 
           SoundOverhaul, WeatherEffects
     Estimated size: 1.8 GB

Merging would reduce 7 archives to 2 (71.4% reduction)
```

**Selective merge:**

If you only want to merge texture mods:

1. Create a separate directory with only texture mods
2. Run merge on that directory

```bash
mkdir texture_mods
mv mods/TexturePack_* texture_mods/
npm start -- merge texture_mods/ -o merged/
```

## Scenario 4: Mod Organizer 2 Integration

If you're using Mod Organizer 2:

```bash
# Windows path example
npm start -- scan "C:/Games/MO2/mods"

# Linux path example
npm start -- scan "$HOME/.wine/drive_c/Games/MO2/mods"
```

**Recommended workflow:**

1. Scan your MO2 mods directory
2. Check what can be merged
3. Create a new MO2 mod folder for merged archives
4. Merge with output to that new mod folder
5. Enable the merged mod in MO2
6. Disable the original mods that were merged

## Scenario 5: Using Custom Output Location

Merge with custom output and options:

```bash
npm start -- merge mods/ \
  --output "/path/to/output" \
  --validate \
  --overwrite
```

Options explained:
- `--output`: Specify where to save merged archives
- `--validate`: Verify merged archives are valid BA2 files
- `--overwrite`: Replace existing merged archives
- `--no-backup`: Skip creating backups (not recommended)

## Best Practices

### 1. Always Backup First

Before merging:
```bash
# Create backup
cp -r mods/ mods_backup/

# Then merge
npm start -- merge mods/ -o merged/
```

### 2. Test Incrementally

Don't merge everything at once:

```bash
# Merge textures first
npm start -- merge texture_mods/ -o merged/

# Test in-game

# Then merge meshes
npm start -- merge mesh_mods/ -o merged/

# Test in-game again
```

### 3. Document Your Merges

Keep track of what you merged:

```bash
npm start -- check mods/ > merge_plan.txt
npm start -- merge mods/ -o merged/ | tee merge_log.txt
```

### 4. Monitor Disk Space

Merged archives may be large:

```bash
# Check available space
df -h merged/

# Check merged file sizes
ls -lh merged/
```

## Troubleshooting Examples

### Problem: "No compatible merge groups found"

**Cause:** All mods have conflicts

**Solution:** Check individual conflicts

```bash
# This will show detailed conflict information
npm start -- check mods/
```

### Problem: Merge fails with "Output file already exists"

**Solution:** Use --overwrite flag

```bash
npm start -- merge mods/ -o merged/ --overwrite
```

### Problem: Want to see what would be merged before doing it

**Solution:** Always use `check` before `merge`

```bash
# See the plan
npm start -- check mods/

# If satisfied, execute
npm start -- merge mods/ -o merged/
```

## Advanced: Scripting Multiple Merges

Create a script for batch merging:

```bash
#!/bin/bash

# merge_all.sh
MODS_DIR="$1"
OUTPUT_DIR="$2"

echo "Scanning mods in $MODS_DIR..."
npm start -- scan "$MODS_DIR"

echo "Checking compatibility..."
npm start -- check "$MODS_DIR"

echo "Executing merge..."
npm start -- merge "$MODS_DIR" -o "$OUTPUT_DIR" --validate

echo "Done! Check $OUTPUT_DIR for merged archives"
```

Usage:
```bash
chmod +x merge_all.sh
./merge_all.sh /path/to/mods /path/to/output
```

## Performance Tips

### For Large Collections (100+ mods)

1. **Group by category first:**
   ```bash
   npm start -- merge mods/textures/ -o merged/
   npm start -- merge mods/meshes/ -o merged/
   npm start -- merge mods/sounds/ -o merged/
   ```

2. **Use SSD for output:**
   - Merging is I/O intensive
   - SSD significantly faster than HDD

3. **Ensure adequate RAM:**
   - Large BA2 files need memory
   - Recommended: 16GB+ for heavy modding

### For Mod Organizer 2 Users

1. Create a dedicated "Merged Mods" category in MO2
2. Place all merged archives in one mod folder
3. Disable original mods after successful merge
4. Keep original mods for reference

## Summary

Mossy Manager makes mod merging safe and efficient:

- ✅ **Scan** to see what you have
- ✅ **Check** to plan merges
- ✅ **Merge** to execute safely
- ✅ **Test** in-game before committing
- ✅ **Document** what you merged
