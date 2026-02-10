# Testing Checklist for Mossy Manager

Use this checklist to verify your Mossy Manager installation works correctly.

## ✅ Installation Verification

### Basic Installation
- [ ] Downloaded/installed Mossy Manager successfully
- [ ] Can run `mossy --help` (or `MossyManager.exe --help`)
- [ ] Can run `mossy --version`
- [ ] Can run `mossy info` and see feature list

### Version Check
Expected output should include:
```
Version: 0.1.0
Features:
  • Load Order Management
  • Conflict Resolution
  • Patching System
```

## ✅ Core Features Testing

### Load Order Management

#### Test with Demo Files
- [ ] Run: `mossy loadorder list --plugins-file demo/profile/plugins.txt`
  - Should display a list of plugins
  - Should show enabled/disabled status
  - Should complete without errors

- [ ] Run: `mossy loadorder validate --plugins-file demo/profile/plugins.txt`
  - Should analyze the load order
  - Should provide statistics
  - Should identify any issues

- [ ] Run: `mossy loadorder optimize --plugins-file demo/profile/plugins.txt --output optimized.txt`
  - Should create an optimized load order
  - Should save to `optimized.txt`
  - Should show before/after comparison

#### Expected Results
- ✓ All commands complete without crashes
- ✓ Output is readable and makes sense
- ✓ Files are created as expected

### Conflict Detection

#### Test with Demo Mods
- [ ] Run: `mossy conflicts scan --mods-dir demo/mods`
  - Should scan mod directories
  - Should detect file conflicts
  - Should categorize by severity

#### Expected Results
- ✓ Finds demo conflicts (if any exist)
- ✓ Provides clear conflict information
- ✓ Shows which mods are involved

### Patching System

#### Create Test Patch
- [ ] Run: `mossy patch create --name "TestPatch" --description "Test patch creation"`
  - Should create a new patch
  - Should save to `patches/TestPatch.json`
  - Should confirm creation

- [ ] Run: `mossy patch list`
  - Should list the created patch
  - Should show patch details

#### Expected Results
- ✓ Patch file created successfully
- ✓ Patch appears in list
- ✓ JSON file is valid

## ✅ Fallout 4 Features (If You Have MO2)

### Prerequisites
Make sure you have:
- [ ] Mod Organizer 2 installed
- [ ] At least one Fallout 4 profile
- [ ] Some mods installed

### Dry Run Test (Safe - No Changes)
- [ ] Run: `mossy fallout4 optimize --profile "Default" --dry-run`
  - Should detect MO2 automatically
  - Should read your load order
  - Should analyze and show recommendations
  - Should NOT make any changes

#### Expected Output
```
[INFO] Detecting Mod Organizer 2...
[SUCCESS] Found MO2 at: [path]
[INFO] Reading profile: Default
[INFO] Found X plugins
[INFO] Analyzing load order...
[INFO] DRY RUN - No changes will be made
```

### Full Optimization (Makes Changes)
⚠️ **Only run this after dry-run succeeds!**

- [ ] Run: `mossy fallout4 optimize --profile "Default"`
  - Should create automatic backup
  - Should optimize load order
  - Should write changes back to MO2

#### Expected Output
```
[INFO] Creating backup...
[SUCCESS] Backup created
[INFO] Optimizing load order...
[SUCCESS] Load order optimized!
[INFO] Writing changes...
[SUCCESS] Complete!
```

### Automatic Workflow
- [ ] Run: `mossy auto --profile "Default"`
  - Should do everything in one command
  - Should optimize load order
  - Should scan for conflicts
  - Should provide recommendations

#### Expected Output
```
[INFO] Starting automatic workflow...
[INFO] Step 1: Optimizing load order...
[SUCCESS] Load order optimized
[INFO] Step 2: Scanning for conflicts...
[INFO] Found X conflicts
[INFO] Step 3: Generating recommendations...
[SUCCESS] Complete! Check reports for details.
```

## ✅ xEdit Integration

### Help and Configuration
- [ ] Run: `mossy conflicts xedit-help`
  - Should display xEdit setup guide
  - Should list supported games
  - Should show installation paths

### Conflict Resolution with xEdit
- [ ] Run: `mossy conflicts resolve-xedit --mods-dir demo/mods --patch-name "TestConflictPatch"`
  - Should export conflicts
  - Should generate Pascal script
  - Should create JSON file

#### Expected Files Created
- `TestConflictPatch_conflicts.json`
- `TestConflictPatch_script.pas`

### Patch Creation with xEdit
- [ ] Run: `mossy patch create-xedit --name "TestXEditPatch" --description "Test patch"`
  - Should create patch file
  - Should generate xEdit script
  - Should save files

## ✅ Advanced Testing

### Command Help
Test that help works for all command groups:
- [ ] `mossy loadorder --help`
- [ ] `mossy conflicts --help`
- [ ] `mossy patch --help`
- [ ] `mossy fallout4 --help`
- [ ] `mossy auto --help`

### Error Handling
Test that errors are handled gracefully:
- [ ] Run command with invalid path: `mossy loadorder list --plugins-file /nonexistent/path.txt`
  - Should show clear error message
  - Should NOT crash

- [ ] Run with missing required argument
  - Should show usage help
  - Should explain what's missing

### Verbose Mode
- [ ] Run any command with `--verbose` or `-v`
  - Should show detailed logging
  - Should show step-by-step progress

## ✅ Integration Testing

### Full Workflow (End-to-End)
If you have a real MO2 setup:

1. [ ] Create backup of your MO2 profile manually (just in case)
2. [ ] Run: `mossy auto --profile "YourProfile"`
3. [ ] Verify MO2 load order was updated
4. [ ] Check conflict reports were generated
5. [ ] Review recommendations
6. [ ] Launch game and verify it works

## 📊 Test Results Summary

Fill this out after testing:

| Category | Status | Notes |
|----------|--------|-------|
| Installation | ⬜ Pass / ⬜ Fail | |
| Load Order Management | ⬜ Pass / ⬜ Fail | |
| Conflict Detection | ⬜ Pass / ⬜ Fail | |
| Patching System | ⬜ Pass / ⬜ Fail | |
| Fallout 4 Features | ⬜ Pass / ⬜ Fail | |
| xEdit Integration | ⬜ Pass / ⬜ Fail | |
| Error Handling | ⬜ Pass / ⬜ Fail | |
| Documentation | ⬜ Pass / ⬜ Fail | |

## 🐛 Reporting Issues

If you encounter problems:

1. **Note the exact command you ran**
2. **Copy the complete error message**
3. **Include your system info**:
   - OS: Windows/Linux/Mac
   - Python version (if applicable): `python --version`
   - Mossy version: `mossy --version`
4. **Check logs** in the current directory
5. **Open an issue** on GitHub with all the above information

## 🎯 Success Criteria

You can consider testing successful if:

✅ All commands run without crashes  
✅ Help text is clear and useful  
✅ Demo files work correctly  
✅ MO2 integration works (if applicable)  
✅ Backup creation works  
✅ Load order optimization produces valid results  
✅ Conflict detection finds actual conflicts  
✅ Generated files are valid  
✅ Documentation matches actual behavior  

## 📝 Additional Notes

Use this space to note anything unusual or interesting:

```
[Your notes here]
```

## ✨ Quick Test Script

For a fast sanity check, run these commands in order:

```bash
# Basic checks
mossy --version
mossy info
mossy --help

# Demo tests
mossy loadorder list --plugins-file demo/profile/plugins.txt
mossy conflicts scan --mods-dir demo/mods
mossy patch create --name "QuickTest" --description "Quick test patch"
mossy patch list

# If you have MO2:
mossy fallout4 optimize --profile "Default" --dry-run
```

If all of these work, you're good to go! 🎉

---

**Need Help?** Check [HOW_TO_DOWNLOAD.md](HOW_TO_DOWNLOAD.md) or [QUICKSTART.md](QUICKSTART.md)
