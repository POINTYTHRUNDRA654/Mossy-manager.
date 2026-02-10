# How to Download and Test Mossy Manager

This guide explains the different ways to get Mossy Manager and start testing.

## 📥 Download Options

### Option 1: Pre-Built Executable (Recommended for Most Users)

**Easiest method - No Python installation required!**

#### For Windows:
1. Go to the [Releases page](https://github.com/POINTYTHRUNDRA654/Mossy-manager./releases)
2. Find the latest release
3. Download `MossyManager-Windows.exe`
4. Save it anywhere on your computer
5. Double-click to run, or use from command line

#### For Linux:
1. Go to the [Releases page](https://github.com/POINTYTHRUNDRA654/Mossy-manager./releases)
2. Find the latest release
3. Download `MossyManager-Linux`
4. Make it executable: `chmod +x MossyManager-Linux`
5. Run it: `./MossyManager-Linux --help`

#### For macOS:
1. Go to the [Releases page](https://github.com/POINTYTHRUNDRA654/Mossy-manager./releases)
2. Find the latest release
3. Download `MossyManager-macOS.dmg`
4. Open the DMG and copy to Applications
5. Run from terminal or Applications folder

### Option 2: Install from Source (For Developers)

**Requires Python 3.8 or higher**

```bash
# Clone the repository
git clone https://github.com/POINTYTHRUNDRA654/Mossy-manager.
cd Mossy-manager.

# Install dependencies
pip install -r requirements.txt

# Install Mossy Manager
pip install -e .

# Test it works
mossy --help
```

### Option 3: Build Your Own Executable

**For advanced users who want to build from source**

```bash
# Clone and install as above
git clone https://github.com/POINTYTHRUNDRA654/Mossy-manager.
cd Mossy-manager.
pip install -r requirements.txt

# Build the executable
python build.py    # Works on all platforms

# Or use the platform-specific script:
# Windows:
build.bat

# Linux/Mac:
./build.sh

# The executable will be in the dist/ folder
```

## 🧪 Quick Test

After downloading/installing, verify it works:

```bash
# If using executable:
MossyManager.exe --help    # Windows
./MossyManager --help      # Linux/Mac

# If installed from source:
mossy --help
```

You should see a help menu listing all available commands.

## 🎮 Test with Your Fallout 4 Setup

### Prerequisites:
- Mod Organizer 2 installed
- At least one profile in MO2
- Some Fallout 4 mods installed

### Safe Test (No Changes Made):

```bash
# Windows executable:
MossyManager.exe fallout4 optimize --profile "Default" --dry-run

# From source:
mossy fallout4 optimize --profile "Default" --dry-run
```

This will analyze your setup without making any changes.

### Full Test (With Backup):

```bash
# Windows executable:
MossyManager.exe auto --profile "Default"

# From source:
mossy auto --profile "Default"
```

This will:
1. Create automatic backups
2. Optimize your load order
3. Scan for conflicts
4. Provide recommendations

## 📁 Test with Demo Data (No MO2 Required)

If you don't have Mod Organizer 2 yet, test with the included demo files:

```bash
# Test load order listing
mossy loadorder list --plugins-file demo/profile/plugins.txt

# Test optimization
mossy loadorder optimize --plugins-file demo/profile/plugins.txt

# Test validation
mossy loadorder validate --plugins-file demo/profile/plugins.txt
```

## 🔍 What to Test

Here's a checklist of things to try:

### Basic Commands:
- [ ] `mossy --version` - Check version
- [ ] `mossy info` - Display capabilities
- [ ] `mossy --help` - View all commands

### Load Order Management:
- [ ] `mossy loadorder list` - List plugins
- [ ] `mossy loadorder validate` - Check for issues
- [ ] `mossy loadorder optimize` - Optimize order

### Fallout 4 Specific:
- [ ] `mossy fallout4 optimize --dry-run` - Preview changes
- [ ] `mossy fallout4 optimize` - Apply optimization
- [ ] `mossy auto` - Complete workflow

### Conflict Detection:
- [ ] `mossy conflicts scan` - Find conflicts
- [ ] `mossy conflicts scan --verbose` - Detailed report

### Patching:
- [ ] `mossy patch create` - Create new patch
- [ ] `mossy patch list` - List patches
- [ ] `mossy patch create-xedit` - xEdit integration

## 📊 Expected Results

### Successful Installation

When you run `mossy info`, you should see:

```
Mossy Manager - MO2 Load Order & Conflict Resolution Tool
Version: 1.0.0
Python: 3.10+

Capabilities:
✓ Load Order Management
✓ Conflict Resolution
✓ Patch Creation & Application
✓ xEdit Integration
✓ Fallout 4 Advanced Support
✓ Mod Organizer 2 Integration
```

### Successful Optimization

When you run `mossy auto`, you should see output like:

```
[INFO] Detecting Mod Organizer 2...
[SUCCESS] Found MO2 at: C:\ModOrganizer2
[INFO] Reading profile: Default
[INFO] Found 47 plugins
[INFO] Optimizing load order...
[SUCCESS] Load order optimized!
[INFO] Scanning for conflicts...
[INFO] Scanned 189 mods
[INFO] Found 42 conflicts (3 critical, 8 high, 31 medium/low)
[INFO] Generated 3 recommendations
[SUCCESS] Complete! Check the reports for details.
```

## ❓ Troubleshooting

### "MossyManager not found"
- Make sure you're in the correct directory
- On Linux/Mac, use `./MossyManager` not just `MossyManager`
- Check the file has execute permissions: `chmod +x MossyManager`

### "Python not found" (Source installation)
- Install Python 3.8 or higher from python.org
- Make sure Python is in your PATH
- Try using `python3` instead of `python`

### "Can't find MO2"
- Specify the path manually: `--mo2-path "C:\Path\To\MO2"`
- Make sure MO2 is installed and has at least one profile
- Check you're using the correct profile name

### "Permission denied"
- Run as administrator (Windows)
- Use `sudo` (Linux/Mac) if needed
- Check file permissions

### "No module named 'click'" (Source installation)
- Install dependencies: `pip install -r requirements.txt`
- Try: `pip install --upgrade -r requirements.txt`

## 🆘 Getting Help

If you encounter issues:

1. **Check Documentation**:
   - [README.md](README.md) - Full documentation
   - [QUICKSTART.md](QUICKSTART.md) - Quick start guide
   - [EXAMPLES.md](EXAMPLES.md) - Usage examples

2. **Enable Verbose Output**:
   ```bash
   mossy auto --verbose --profile "Default"
   ```

3. **Check Logs**:
   - Mossy creates detailed logs in the current directory
   - Look for error messages

4. **Report Issues**:
   - Open an issue on [GitHub](https://github.com/POINTYTHRUNDRA654/Mossy-manager./issues)
   - Include your OS, Python version (if applicable), and error message
   - Attach log files if available

## ✅ You're Ready!

Once you can successfully run `mossy --help` and see the command list, you're all set!

Next steps:
- Read [QUICKSTART.md](QUICKSTART.md) for common use cases
- Check [FALLOUT4_COMPLETE.md](FALLOUT4_COMPLETE.md) for FO4-specific features
- Explore [EXAMPLES.md](EXAMPLES.md) for real-world scenarios

## 🎯 Quick Links

- 📦 [Download Latest Release](https://github.com/POINTYTHRUNDRA654/Mossy-manager./releases/latest)
- 📖 [Full Documentation](README.md)
- 🚀 [Quick Start Guide](QUICKSTART.md)
- 💡 [Usage Examples](EXAMPLES.md)
- 🐛 [Report Issues](https://github.com/POINTYTHRUNDRA654/Mossy-manager./issues)

---

**Ready to optimize your Fallout 4 setup?** Download now and run `mossy auto`!
