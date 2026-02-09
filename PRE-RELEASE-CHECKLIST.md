# Pre-Release Testing Checklist

This is a quick checklist for testing Mossy Manager before creating a release.

## Quick Test (5 minutes)

### 1. Run Automated Tests
```bash
python3 test_mossy_manager.py
```
**Expected**: All 18 tests pass ✓

### 2. Run Demo Script
```bash
python3 demo.py
```
**Expected**: Demo creates test structure and all checks pass ✓

### 3. Build Executable
```bash
# Linux/Mac
./build.sh

# Windows
build.bat
```
**Expected**: Build completes successfully, executable created in `dist/` folder ✓

## Manual Test (10 minutes)

### 1. Launch Application
```bash
python3 mossy_manager.py
# OR
./dist/MossyManager
```

### 2. Test Basic Workflow

Use the demo structure created by `demo.py`:
```bash
# The demo creates test MO2 at:
# /tmp/mossy_manager_demo/ModOrganizer2
```

1. **Set MO2 Path**
   - Click "Browse..."
   - Select: `/tmp/mossy_manager_demo/ModOrganizer2` (or your demo path)
   - ✓ Path should appear in text field

2. **Refresh Mods**
   - Click "Refresh Mods" button
   - ✓ Should see 8 sample mods listed
   - ✓ Status bar shows "Found 8 mods"

3. **Test Settings**
   - Go to Settings tab
   - Check "Auto-launch MO2 on startup"
   - Change theme to "Dark"
   - Click "Save Settings"
   - ✓ Success message appears

4. **Test Persistence**
   - Close application
   - Reopen application
   - ✓ MO2 path is still set
   - ✓ Settings are still saved

## Full Test (30 minutes)

See [TESTING.md](TESTING.md) for comprehensive testing guide.

## Before Creating a Release

- [ ] All automated tests pass
- [ ] Demo script runs successfully
- [ ] Executable builds without errors
- [ ] Manual test workflow completes successfully
- [ ] Settings persist across sessions
- [ ] Version number updated (if applicable)
- [ ] README and documentation are up to date

## Release Process

Once all tests pass:

1. **Create a git tag**:
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

2. **GitHub Actions will automatically**:
   - Run tests on all platforms
   - Build executables for Windows, Linux, and macOS
   - Create a GitHub release
   - Upload executables as release assets

3. **Verify the release**:
   - Go to GitHub releases page
   - Download executables for each platform
   - Test at least one platform

## Quick Reference

| Command | Purpose |
|---------|---------|
| `python3 test_mossy_manager.py` | Run automated tests |
| `python3 demo.py` | Create demo structure |
| `python3 mossy_manager.py` | Run from source |
| `./build.sh` or `build.bat` | Build executable |
| `./dist/MossyManager` | Run executable |

## Test Results

Record your test results:

```
Date: ___________
Tester: ___________

[ ] Automated tests passed
[ ] Demo script passed
[ ] Build successful
[ ] Manual workflow passed
[ ] Settings persist
[ ] Ready for release

Notes:
_________________________________
_________________________________
_________________________________
```

## Getting Help

- See [TESTING.md](TESTING.md) for detailed testing instructions
- See [README.md](README.md) for usage documentation
- Report issues on GitHub: https://github.com/POINTYTHRUNDRA654/Mossy-manager./issues
