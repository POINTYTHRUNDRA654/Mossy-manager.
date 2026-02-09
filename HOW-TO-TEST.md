# HOW TO TEST MOSSY MANAGER

This guide shows you exactly how to test Mossy Manager before release.

## Option 1: Quick Automated Test (2 minutes)

Just run the automated test suite:

```bash
python3 test_mossy_manager.py
```

You should see:
```
Tests run: 18
Successes: 18
Failures: 0
Errors: 0
```

✅ If all 18 tests pass, core functionality is working!

---

## Option 2: Test with Demo Data (5 minutes)

### Step 1: Create Test Data
```bash
python3 demo.py
```

This creates a fake MO2 installation with 8 sample mods at:
- **Linux/Mac**: `/tmp/mossy_manager_demo/ModOrganizer2`
- **Windows**: `%TEMP%\mossy_manager_demo\ModOrganizer2`

### Step 2: Launch the App
```bash
python3 mossy_manager.py
```

OR if you built the executable:
```bash
./dist/MossyManager          # Linux/Mac
dist\MossyManager.exe        # Windows
```

### Step 3: Test the App
1. Click **"Browse..."** button
2. Select the path from Step 1 (the demo MO2 folder)
3. Click **"Refresh Mods"**
4. ✅ You should see 8 sample mods listed!

### Step 4: Test Settings
1. Go to **Settings** tab
2. Enable **"Auto-launch MO2 on startup"**
3. Change **Theme** to "Dark"
4. Click **"Save Settings"**
5. Close and reopen the app
6. ✅ Your settings should be saved!

---

## Option 3: Test with Real MO2 (10 minutes)

If you have Mod Organizer 2 installed:

### Step 1: Launch the App
```bash
python3 mossy_manager.py
```

### Step 2: Point to Your MO2
1. Click **"Browse..."**
2. Select your MO2 installation folder (contains ModOrganizer.exe)
3. Click **"Refresh Mods"**
4. ✅ Your real mods should appear!

### Step 3: Test Launch
1. Click **"Launch MO2"**
2. ✅ Mod Organizer 2 should start!

---

## Building and Testing the Executable

### Build
```bash
# Linux/Mac
./build.sh

# Windows
build.bat
```

### Test the Executable
The executable will be in the `dist/` folder:

```bash
# Linux/Mac
./dist/MossyManager

# Windows
dist\MossyManager.exe
```

Test it the same way as Option 2 or 3 above!

---

## What to Check

When testing, verify these work:

- [ ] App launches without errors
- [ ] Can browse and select MO2 path
- [ ] Mods are discovered and listed
- [ ] Settings can be saved
- [ ] Settings persist after restart
- [ ] "Launch MO2" button works (if you have real MO2)
- [ ] Status bar shows correct messages

---

## If Something Doesn't Work

### Tests Fail
If `test_mossy_manager.py` shows failures:
1. Check the error messages
2. Run with verbose output: `python3 -m unittest test_mossy_manager -v`
3. Report the issue with the test output

### App Won't Launch
```bash
# Try running with error output
python3 mossy_manager.py 2>&1 | tee error.log
```

### No Mods Show Up
- Make sure you selected a valid MO2 folder
- The folder should contain `ModOrganizer.exe`
- The folder should have a `mods/` subdirectory
- Check status bar for error messages

### Build Fails
- Make sure PyInstaller is installed: `pip install pyinstaller`
- Check that all dependencies are met: `pip install -r requirements.txt`
- Try cleaning first: `rm -rf build dist` then rebuild

---

## Getting Help

1. **Check Documentation**:
   - `TESTING.md` - Detailed testing guide
   - `README.md` - General documentation
   - `PRE-RELEASE-CHECKLIST.md` - Release checklist

2. **Report Issues**: https://github.com/POINTYTHRUNDRA654/Mossy-manager./issues

3. **Include**:
   - What you were testing
   - What you expected to happen
   - What actually happened
   - Error messages (if any)
   - Your OS and Python version

---

## Ready to Release?

Once you've tested everything:

1. ✅ All automated tests pass
2. ✅ Manual testing successful
3. ✅ Executable builds and runs
4. ✅ Settings persist correctly

Then follow the release process in `RELEASING.md`!

---

**Quick Reference**:
- Run tests: `python3 test_mossy_manager.py`
- Create demo: `python3 demo.py`
- Run app: `python3 mossy_manager.py`
- Build: `./build.sh` or `build.bat`
