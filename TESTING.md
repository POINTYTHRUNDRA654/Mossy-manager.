# Testing Guide for Mossy Manager

This guide provides comprehensive testing instructions for Mossy Manager before release.

## Automated Tests

### Running Unit Tests

The project includes a comprehensive unit test suite that tests core functionality without requiring a GUI.

```bash
# Run all tests
python3 test_mossy_manager.py

# Run with Python's unittest module
python3 -m unittest test_mossy_manager -v
```

### Test Coverage

The test suite covers:
- ✅ Settings management (loading, saving, defaults)
- ✅ Path validation and MO2 directory structure
- ✅ Mod discovery and listing
- ✅ Cross-platform launch mechanisms
- ✅ Configuration file operations
- ✅ Error handling for invalid inputs

## Manual Testing

### Prerequisites

Before testing, ensure you have:
1. Python 3.8+ installed
2. A Mod Organizer 2 installation (or test directory structure)
3. The executable built or source code ready to run

### Building the Executable

```bash
# Linux/macOS
./build.sh

# Windows
build.bat
```

### Test Plan

#### 1. First Launch Test
**Objective**: Verify the application launches correctly and creates default configuration.

**Steps**:
1. Launch the application: `python3 mossy_manager.py` or run the executable
2. Verify the main window appears with three tabs (Manager, Settings, About)
3. Check that `~/.mossy_manager/config.json` is created

**Expected Results**:
- Application window opens without errors
- Default settings are initialized
- Configuration directory is created

#### 2. MO2 Path Configuration Test
**Objective**: Test MO2 path selection and validation.

**Steps**:
1. Click "Browse..." button in the Manager tab
2. Select your MO2 installation directory
3. Click "Refresh Mods" button

**Expected Results**:
- File browser opens correctly
- Selected path is displayed in the text field
- Status bar shows "MO2 path set to: [path]"
- If valid MO2 path, mods are listed

#### 3. Mod List Test
**Objective**: Verify mod discovery and display.

**Setup**: Use a valid MO2 installation with mods, or create a test structure:
```
/path/to/MO2/
├── ModOrganizer.exe
└── mods/
    ├── Mod1/
    ├── Mod2/
    └── Mod3/
```

**Steps**:
1. Set MO2 path to your installation
2. Click "Refresh Mods"
3. Verify mods appear in the list
4. Check that only directories are listed (not files)
5. Verify mods are sorted alphabetically

**Expected Results**:
- All mod folders are displayed
- Files in mods directory are ignored
- List is sorted alphabetically
- Status bar shows count of mods found

#### 4. Launch MO2 Test
**Objective**: Test the MO2 launch functionality.

**Prerequisites**: Valid MO2 installation with `ModOrganizer.exe`

**Steps**:
1. Set valid MO2 path
2. Click "Launch MO2" button
3. Verify MO2 application starts

**Expected Results**:
- MO2 launches successfully
- Status bar shows "Launching Mod Organizer 2..."
- No errors displayed

**Test Cases**:
- ✅ Valid MO2 path
- ✅ Invalid path (should show error)
- ✅ Missing ModOrganizer.exe (should show error)

#### 5. Settings Persistence Test
**Objective**: Verify settings are saved and loaded correctly.

**Steps**:
1. Set MO2 path
2. Go to Settings tab
3. Enable "Auto-launch MO2 on startup"
4. Change Theme to "Dark"
5. Click "Save Settings"
6. Close the application
7. Reopen the application

**Expected Results**:
- MO2 path is retained
- Auto-launch checkbox is checked
- Theme selection is "Dark"
- Settings persist across sessions

#### 6. Error Handling Test
**Objective**: Verify the application handles errors gracefully.

**Test Cases**:
1. **No MO2 path set**:
   - Try to launch MO2 without setting path
   - Expected: Error message displayed

2. **Invalid MO2 path**:
   - Set path to non-existent directory
   - Click "Refresh Mods"
   - Expected: Warning about missing mods directory

3. **Missing ModOrganizer.exe**:
   - Set path to directory without `ModOrganizer.exe`
   - Click "Launch MO2"
   - Expected: Error message displayed

#### 7. Cross-Platform Test
**Objective**: Verify platform-specific functionality works.

**Platforms to test**:
- ✅ Windows (os.startfile)
- ✅ macOS (open command)
- ✅ Linux (xdg-open command)

**Steps** (per platform):
1. Build executable for the platform
2. Run all tests from Test Plan
3. Verify launch mechanism works correctly

#### 8. Executable Test
**Objective**: Verify the built executable works as standalone application.

**Steps**:
1. Build the executable
2. Copy to a clean directory (without source files)
3. Run the executable
4. Perform all tests from the test plan

**Expected Results**:
- Executable runs without requiring Python
- All functionality works identically to source version
- No dependency errors

## Regression Testing

Before each release, run through this checklist:

- [ ] All automated tests pass
- [ ] Application launches successfully
- [ ] MO2 path can be set and saved
- [ ] Mods are discovered and listed correctly
- [ ] MO2 can be launched
- [ ] Settings persist across sessions
- [ ] Error messages display correctly
- [ ] About tab shows correct version
- [ ] Executable builds without errors
- [ ] Executable runs on target platforms

## Performance Testing

### Startup Time
- Application should launch within 2-3 seconds
- Configuration loading should be near-instantaneous

### Mod List Loading
- Should handle 100+ mods without noticeable delay
- Refresh operation should complete within 1 second for typical installations

### Memory Usage
- Idle memory usage should be < 50MB
- Should not have memory leaks during extended use

## Reporting Issues

When reporting test failures, include:
1. **Platform**: OS and version
2. **Python Version**: Output of `python3 --version`
3. **Steps to Reproduce**: Exact steps that cause the issue
4. **Expected Behavior**: What should happen
5. **Actual Behavior**: What actually happens
6. **Logs**: Any error messages or stack traces
7. **Screenshots**: If applicable

## Test Environment Setup

### Creating a Test MO2 Structure

If you don't have MO2 installed, create a test structure:

```bash
# Linux/macOS
mkdir -p ~/test-mo2/mods/{TestMod1,TestMod2,TestMod3}
touch ~/test-mo2/ModOrganizer.exe

# Windows
mkdir C:\test-mo2\mods\TestMod1
mkdir C:\test-mo2\mods\TestMod2
mkdir C:\test-mo2\mods\TestMod3
echo. > C:\test-mo2\ModOrganizer.exe
```

Then use `~/test-mo2` or `C:\test-mo2` as your MO2 path for testing.

## Continuous Integration

The project includes GitHub Actions workflow that:
- Builds executables for Windows, Linux, and macOS
- Runs automated tests on all platforms
- Creates releases with build artifacts

Check the Actions tab on GitHub for build status.

## Release Checklist

Before releasing a new version:

1. [ ] Update version number in About tab
2. [ ] Run all automated tests
3. [ ] Complete manual testing on at least one platform
4. [ ] Build executables for all platforms
5. [ ] Test executables on each platform
6. [ ] Update CHANGELOG (if exists)
7. [ ] Create git tag
8. [ ] Verify GitHub Actions build succeeds
9. [ ] Download and test release artifacts
10. [ ] Update documentation if needed

## Getting Help

If you encounter issues during testing:
1. Check the [Issues](https://github.com/POINTYTHRUNDRA654/Mossy-manager./issues) page
2. Review existing issues for similar problems
3. Create a new issue with detailed information
4. Include test results and environment details
