# Mossy Manager Examples

This directory contains example files demonstrating how to use Mossy Manager.

## Example 1: Load Order Management

### View your current load order
```bash
mossy loadorder list --plugins-file demo/profile/plugins.txt
```

This will display:
- Total plugin count and statistics
- Enabled/disabled status for each plugin
- Plugin types (Master, Light, Regular)
- Current priority order

### Validate your load order
```bash
mossy loadorder validate --plugins-file demo/profile/plugins.txt
```

This checks for common issues like:
- Master files loading after regular plugins
- Missing plugins in load order
- Other load order inconsistencies

### Optimize your load order
```bash
mossy loadorder optimize --plugins-file demo/profile/plugins.txt --output optimized_loadorder.txt
```

This automatically sorts plugins:
1. Master files (.esm) first
2. Light plugins (.esl) second
3. Regular plugins (.esp) last

## Example 2: Conflict Detection

### Create test mod directories
```bash
mkdir -p demo/mods/ModA/textures
mkdir -p demo/mods/ModB/textures
echo "ModA texture" > demo/mods/ModA/textures/test.dds
echo "ModB texture" > demo/mods/ModB/textures/test.dds
```

### Scan for conflicts
```bash
mossy conflicts scan --mods-dir demo/mods --output conflict_report.txt
```

This will:
- Scan all mod directories
- Detect files present in multiple mods
- Classify conflicts by severity
- Generate a detailed report

## Example 3: Patching

### Create a new patch
```bash
mossy patch create --name "MyCompatibilityPatch" --description "Fixes texture conflicts"
```

### Edit the patch file
Open `patches/MyCompatibilityPatch.json` and add operations:

```json
{
  "name": "MyCompatibilityPatch",
  "description": "Fixes texture conflicts",
  "operations": [
    {
      "type": "merge",
      "file": "Data/config.ini",
      "content": "[Settings]\nCompatMode=1"
    },
    {
      "type": "replace",
      "file": "Data/scripts/init.txt",
      "content": "# Updated initialization script"
    }
  ],
  "target_mods": ["ModA", "ModB"]
}
```

### Test the patch (dry run)
```bash
mossy patch apply --patch-file patches/MyCompatibilityPatch.json --mod-dir demo/mods/ModA --dry-run
```

### Apply the patch
```bash
mossy patch apply --patch-file patches/MyCompatibilityPatch.json --mod-dir demo/mods/ModA
```

## Example 4: xEdit Integration for Conflict Resolution

### Get xEdit help
```bash
mossy conflicts xedit-help
```

### Create conflicts for testing
```bash
mkdir -p demo/mods/WeatherMod/textures
mkdir -p demo/mods/LightingMod/textures
echo "weather sky" > demo/mods/WeatherMod/textures/sky.dds
echo "lighting sky" > demo/mods/LightingMod/textures/sky.dds
echo "plugin1" > demo/mods/WeatherMod/WeatherMod.esp
echo "plugin2" > demo/mods/LightingMod/LightingMod.esp
```

### Resolve conflicts with xEdit (auto-launch)
```bash
mossy conflicts resolve-xedit \
  --mods-dir demo/mods \
  --xedit-path "C:/Modding/Tools/SSEEdit/SSEEdit.exe" \
  --patch-name "Weather_Lighting_Patch" \
  --game skyrimse \
  --auto-launch
```

### Resolve conflicts with xEdit (manual)
```bash
# Generate xEdit files without launching
mossy conflicts resolve-xedit \
  --mods-dir demo/mods \
  --patch-name "Weather_Lighting_Patch" \
  --output-dir ./xedit_patches

# Review generated files
ls -l xedit_patches/
cat xedit_patches/Weather_Lighting_Patch_conflicts.json

# Then open xEdit manually and use the generated script
```

### xEdit Workflow
1. Run `mossy conflicts resolve-xedit` to detect conflicts and generate files
2. xEdit opens automatically (if --auto-launch is used)
3. In xEdit:
   - Right-click and select "Apply Script"
   - Choose the generated `.pas` script
   - Or manually create a new patch plugin
   - Copy conflicting records to your patch
   - Resolve conflicts by choosing which version to keep
4. Save and close xEdit
5. Add the new patch to your load order (after conflicting mods)

## Example 5: Creating Patches with xEdit

### Create a new patch with xEdit integration
```bash
mossy patch create-xedit \
  --name "MyGameplayPatch" \
  --description "Custom gameplay balance changes" \
  --target-plugin "MyGameplayPatch.esp" \
  --output-dir ./xedit_patches
```

This will:
- Create a Mossy Manager patch
- Generate xEdit-compatible files
- Prepare a script for xEdit

### Export existing patch to xEdit
```bash
# First create a regular patch
mossy patch create --name "WeaponBalance" --description "Weapon damage adjustments"

# Add operations manually by editing patches/WeaponBalance.json
# Then export to xEdit format
mossy patch export-xedit \
  --patch-file patches/WeaponBalance.json \
  --target-plugin "WeaponBalance.esp" \
  --output-dir ./xedit_patches
```

### Using the generated files in xEdit
1. Open xEdit (SSEEdit, TES5Edit, etc.)
2. Right-click on the left panel
3. Select "Apply Script"
4. Choose the generated `_apply.pas` script
5. The script will create/load the target plugin
6. Add your modifications to the plugin
7. Save and close xEdit
8. Add the plugin to your load order

### Example: Complete patch workflow
```bash
# Step 1: Create patch with xEdit
mossy patch create-xedit \
  --name "CombatOverhaul" \
  --description "Comprehensive combat changes" \
  --xedit-path "C:/Tools/SSEEdit/SSEEdit.exe" \
  --game skyrimse \
  --auto-launch

# Step 2: (xEdit opens automatically)
# - Edit records as needed
# - Make your changes
# - Save and close

# Step 3: Test the patch in-game
# Add CombatOverhaul.esp to your load order

# Step 4: If needed, export again for further editing
mossy patch export-xedit \
  --patch-file patches/CombatOverhaul.json \
  --xedit-path "C:/Tools/SSEEdit/SSEEdit.exe" \
  --auto-launch
```

## Example 6: Complete Workflow

### Step 1: Check current state
```bash
mossy loadorder list --plugins-file plugins.txt
mossy loadorder validate --plugins-file plugins.txt
```

### Step 2: Scan for conflicts
```bash
mossy conflicts scan --mods-dir /path/to/MO2/mods --output conflicts.txt
```

### Step 3: Review conflicts
```bash
cat conflicts.txt
```

### Step 4: Optimize load order
```bash
mossy loadorder optimize --plugins-file plugins.txt --output new_loadorder.txt
```

### Step 5: Create conflict resolution patch with xEdit
```bash
mossy conflicts resolve-xedit \
  --mods-dir /path/to/MO2/mods \
  --xedit-path "C:/Tools/SSEEdit/SSEEdit.exe" \
  --patch-name "ConflictResolution_Patch" \
  --auto-launch
```

### Step 6: Manual patches if needed
```bash
mossy patch create --name "ModA_ModB_Compat" --description "Compatibility between ModA and ModB"
# Edit the patch file
mossy patch apply --patch-file patches/ModA_ModB_Compat.json --mod-dir /path/to/mod
```

## Tips

1. **Always backup** your plugins.txt and mod files before making changes
2. **Use --dry-run** when applying patches to test them first
3. **Enable verbose logging** with `-v` flag for detailed information
4. **Check validation** after optimizing load order
5. **Review conflict reports** to understand which mods need compatibility patches
6. **Use xEdit for complex conflicts** - It's the most powerful tool for plugin conflicts
7. **Test in-game** after creating conflict patches to ensure everything works

## Real-World MO2 Paths

### Windows (typical MO2 installation)
- Plugins: `C:\Users\YourName\AppData\Local\ModOrganizer\profiles\Default\plugins.txt`
- Load Order: `C:\Users\YourName\AppData\Local\ModOrganizer\profiles\Default\loadorder.txt`
- Mods: `C:\Modding\ModOrganizer2\mods`

### Example with real paths
```bash
mossy loadorder list --plugins-file "C:\Users\YourName\AppData\Local\ModOrganizer\profiles\Default\plugins.txt"
mossy conflicts scan --mods-dir "C:\Modding\ModOrganizer2\mods"
```

## Troubleshooting

### Issue: "No plugins loaded"
- Check that the plugins.txt file exists and is not empty
- Verify the file path is correct
- Make sure the file is in the correct format

### Issue: "Mods directory not found"
- Verify the path to your MO2 mods directory
- Check that the directory contains mod subdirectories

### Issue: "Patch validation failed"
- Review the error messages
- Check that target files exist
- Verify the patch JSON syntax is correct

For more help, run:
```bash
mossy --help
mossy loadorder --help
mossy conflicts --help
mossy patch --help
```
