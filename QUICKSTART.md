# Mossy Manager - Quick Start Guide

Get started with Mossy Manager in under 5 minutes!

## 🚀 For First-Time Users (Easiest Way)

### Step 1: Get Mossy Manager

Choose one of these options:

#### Option A: Download Executable (No Python Required!) ⭐ RECOMMENDED

1. Go to the [latest release](https://github.com/POINTYTHRUNDRA654/Mossy-manager./releases/tag/latest)
2. Click **MossyManager.exe** to download it (Windows) or `MossyManager` (Linux/Mac)
3. Save it anywhere on your computer (e.g. `C:\Tools\MossyManager\`)
4. That's it! No installation needed!

**To use inside Mod Organizer 2:**
- Open MO2 → gear icon (⚙) → Executables → **+**
- Title: `Mossy Manager`, Binary: path to `MossyManager.exe`
- Arguments: `auto --profile "Default"`
- Click OK, then select it from the Run dropdown

#### Option B: Install from Source (For Developers)

> ⚠️ **Windows users:** The repo name ends with a `.` which Windows does not allow as a
> folder name. Clone from Command Prompt with a custom folder name:
>
> ```cmd
> git clone https://github.com/POINTYTHRUNDRA654/Mossy-manager. MossyManager
> cd MossyManager
> install.bat
> ```

```bash
# Clone the repository (Linux/macOS)
git clone https://github.com/POINTYTHRUNDRA654/Mossy-manager. MossyManager
cd MossyManager

# Install dependencies and set up
./install.sh

# Or manually:
pip install -r requirements.txt
pip install -e .
```

### Step 2: Test Basic Functionality

Open a terminal/command prompt where you saved the file and run:

```bash
# If you downloaded the executable:
MossyManager.exe --help    # Windows
./MossyManager --help      # Linux/Mac

# If you installed from source:
mossy --help
```

You should see the help menu with all available commands!

### Step 3: Try the Info Command

```bash
# Executable:
MossyManager.exe info

# From source:
mossy info
```

This displays Mossy Manager version and capabilities.

### Step 4: Launch the UI (LOOT-style)

Run the local web UI (no cloud, opens your browser):

```bash
# Executable:
MossyManager.exe ui --open

# From source:
mossy ui --open
```

The UI starts a local server on http://127.0.0.1:8732/, detects MO2, and lets you preview/apply load order optimization and run conflict scans. Apply is opt-in; keep "Apply" unchecked for dry-run previews.

## 🎮 For Fallout 4 Users (Automatic Optimization)

### Prerequisites
- Mod Organizer 2 installed
- At least one Fallout 4 profile in MO2
- Some mods installed

### Quick Test (Dry Run)

Test Mossy Manager without making any changes:

```bash
# Windows executable:
MossyManager.exe fallout4 optimize --profile "Default" --dry-run

# From source:
mossy fallout4 optimize --profile "Default" --dry-run
```

This will:
- ✓ Auto-detect your MO2 installation
- ✓ Read your current load order
- ✓ Analyze and show what would be changed
- ✗ NOT make any actual changes (safe!)

### Full Automatic Workflow

Once you're comfortable, run the complete optimization:

```bash
# Windows executable:
MossyManager.exe auto --profile "Default"

# From source:
mossy auto --profile "Default"
```

This single command will:
1. Detect MO2 installation
2. Optimize your load order
3. Scan for conflicts
4. Provide recommendations
5. Create backups automatically

**Result**: Your game is optimized for maximum stability!

## 📁 Test with Sample Data

If you don't have MO2 installed yet, you can test with the demo files:

```bash
# List demo plugins
MossyManager.exe loadorder list --plugins-file demo/profile/plugins.txt

# Optimize demo load order
MossyManager.exe loadorder optimize --plugins-file demo/profile/plugins.txt
```

## 🔍 Common Commands

### Load Order Management

```bash
# List current load order
mossy loadorder list --plugins-file path/to/plugins.txt

# Validate load order
mossy loadorder validate --plugins-file path/to/plugins.txt

# Optimize load order
mossy loadorder optimize --plugins-file path/to/plugins.txt
```

### Conflict Detection

```bash
# Scan for conflicts
mossy conflicts scan --mods-dir path/to/mods

# Get detailed report
mossy conflicts scan --mods-dir path/to/mods --verbose
```

### Patching

```bash
# Create a patch
mossy patch create --name "MyPatch"

# Apply a patch
mossy patch apply --patch-file patches/MyPatch.json --mod-dir path/to/mod
```

## ❓ Troubleshooting

### Can't find MO2?

Specify the path manually:

```bash
mossy fallout4 optimize --mo2-path "C:\Games\ModOrganizer2" --profile "Default"
```

### Want to see what Mossy will do first?

Use `--dry-run` flag:

```bash
mossy fallout4 optimize --profile "Default" --dry-run
```

### Need help with a specific command?

Add `--help` to any command:

```bash
mossy loadorder --help
mossy fallout4 optimize --help
mossy auto --help
```

## 🎯 What's Next?

1. **Read the Full Documentation**: Check out [README.md](README.md) for detailed features
2. **Explore Examples**: See [EXAMPLES.md](EXAMPLES.md) for real-world scenarios
3. **Fallout 4 Guide**: Read [FALLOUT4_COMPLETE.md](FALLOUT4_COMPLETE.md) for advanced FO4 features
4. **xEdit Integration**: Learn about [XEDIT_INTEGRATION.md](XEDIT_INTEGRATION.md) for advanced patching

## 💡 Pro Tips

- **Always backup first**: Mossy creates backups automatically, but you can also backup manually
- **Start with dry-run**: Test commands with `--dry-run` before making changes
- **Use auto command**: `mossy auto` does everything in one command!
- **Check verbose output**: Add `--verbose` to see detailed information
- **Read the logs**: Mossy provides detailed output about what it's doing

## 🆘 Need Help?

- 📖 Check [README.md](README.md) for full documentation
- 💬 Open an issue on [GitHub](https://github.com/POINTYTHRUNDRA654/Mossy-manager./issues)
- 📚 See [EXAMPLES.md](EXAMPLES.md) for common use cases

## ✅ Testing Checklist

Use this to verify everything works:

- [ ] Downloaded/installed Mossy Manager
- [ ] Ran `--help` command successfully
- [ ] Ran `info` command
- [ ] Tested with demo files (if no MO2)
- [ ] Ran `--dry-run` on your setup (if you have MO2)
- [ ] Verified MO2 auto-detection works
- [ ] Successfully optimized load order
- [ ] Scanned for conflicts
- [ ] Reviewed recommendations

**All working?** 🎉 You're ready to optimize your game!

## 🚀 Most Common Use Case

For most Fallout 4 users, this is all you need:

```bash
# Download MossyManager.exe from Releases
# Open command prompt in the same folder
# Run this one command:
MossyManager.exe auto --profile "Default"

# That's it! Your game is optimized!
```

---

**Questions?** Open an issue or check the documentation files!
