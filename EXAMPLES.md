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

## Example 4: Complete Workflow

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

### Step 5: Create compatibility patches if needed
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
