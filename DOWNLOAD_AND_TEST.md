# 📥 How to Download and Test Mossy Manager

## Quick Answer: 3 Simple Steps

### 1️⃣ Download
Go to the [Releases Page](https://github.com/POINTYTHRUNDRA654/Mossy-manager./releases/latest) and download:
- **Windows**: `MossyManager-Windows.exe`
- **Linux**: `MossyManager-Linux`
- **macOS**: `MossyManager-macOS.dmg`

### 2️⃣ Run
```bash
# Windows
MossyManager.exe --help

# Linux/Mac
./MossyManager --help
```

### 3️⃣ Test
```bash
# Quick test with demo data (no MO2 needed)
MossyManager.exe loadorder list --plugins-file demo/profile/plugins.txt

# Or optimize your Fallout 4 setup automatically
MossyManager.exe auto --profile "Default"
```

That's it! 🎉

---

## Detailed Instructions

### Option A: Pre-Built Executable (Easiest!)

**No Python installation required!**

1. **Download**
   - Visit: https://github.com/POINTYTHRUNDRA654/Mossy-manager./releases/latest
   - Click on the file for your operating system:
     - Windows: `MossyManager-Windows.exe`
     - Linux: `MossyManager-Linux`
     - macOS: `MossyManager-macOS.dmg`

2. **Save and Run**
   - Windows: Just double-click or run from command prompt
   - Linux: `chmod +x MossyManager-Linux && ./MossyManager-Linux`
   - macOS: Open the DMG and copy to Applications

3. **Verify Installation**
   ```bash
   MossyManager.exe --version
   MossyManager.exe info
   ```

### Option B: Install from Source (For Developers)

**Requires Python 3.8+**

```bash
# Clone repository
git clone https://github.com/POINTYTHRUNDRA654/Mossy-manager.
cd Mossy-manager.

# Install dependencies
pip install -r requirements.txt

# Install Mossy Manager
pip install -e .

# Test it
mossy --version
mossy info
```

### Option C: Build Your Own Executable

```bash
# After cloning and installing dependencies:
python build.py

# Executable will be in dist/ folder
# Windows: dist/MossyManager.exe
# Linux/Mac: dist/MossyManager
```

---

## Testing Without Mod Organizer 2

You can test all features using the included demo files:

```bash
# Test load order management
MossyManager.exe loadorder list --plugins-file demo/profile/plugins.txt
MossyManager.exe loadorder validate --plugins-file demo/profile/plugins.txt
MossyManager.exe loadorder optimize --plugins-file demo/profile/plugins.txt

# Test conflict detection
MossyManager.exe conflicts scan --mods-dir demo/mods

# Test patching
MossyManager.exe patch create --name "TestPatch"
MossyManager.exe patch list
```

---

## Testing With Mod Organizer 2 (Fallout 4)

### Safe Test (No Changes)

Test with the `--dry-run` flag to see what would happen:

```bash
MossyManager.exe fallout4 optimize --profile "Default" --dry-run
```

This will:
- ✓ Auto-detect your MO2 installation
- ✓ Analyze your load order
- ✓ Show what changes would be made
- ✗ NOT make any actual changes

### Full Optimization

When you're ready to optimize:

```bash
# Complete automatic workflow (recommended!)
MossyManager.exe auto --profile "Default"
```

This single command will:
1. Create automatic backups
2. Optimize your load order using Fallout 4 rules
3. Scan for conflicts
4. Generate recommendations
5. Provide detailed reports

Or use individual commands:

```bash
# Just optimize load order
MossyManager.exe fallout4 optimize --profile "Default"

# Just scan for conflicts
MossyManager.exe conflicts scan --mods-dir "C:\MO2\mods"

# Manual MO2 path (if auto-detection fails)
MossyManager.exe fallout4 optimize --mo2-path "C:\Games\MO2" --profile "Default"
```

---

## What You Should See

### Successful Installation

```
$ MossyManager.exe info

╔═══════════════════════════════════════════════════════════╗
║           MOSSY MANAGER - MO2 Management Tool            ║
╚═══════════════════════════════════════════════════════════╝

Version: 0.1.0

Features:
  • Load Order Management
  • Conflict Resolution
  • Patching System
```

### Successful Optimization

```
$ MossyManager.exe auto --profile "Default"

[INFO] Detecting Mod Organizer 2...
[SUCCESS] Found MO2 at: C:\ModOrganizer2
[INFO] Found 47 plugins
[INFO] Optimizing load order...
[SUCCESS] Load order optimized!
[INFO] Scanning for conflicts...
[INFO] Found 42 conflicts (3 critical, 8 high)
[SUCCESS] Complete! Your game is optimized!
```

---

## Troubleshooting

### "Command not found" or "File not found"

**Windows:**
- Make sure you're in the same directory as the .exe file
- Or add the directory to your PATH

**Linux/Mac:**
- Make the file executable: `chmod +x MossyManager`
- Run with `./MossyManager` not just `MossyManager`

### "Can't find MO2"

Specify the path manually:
```bash
MossyManager.exe fallout4 optimize --mo2-path "C:\Your\Path\To\MO2" --profile "Default"
```

### "Python not found" (Source Installation)

- Install Python 3.8+ from python.org
- Make sure it's in your PATH
- Try `python3` instead of `python`

### "Permission denied"

- Windows: Run as Administrator
- Linux/Mac: Use `sudo` or check file permissions

---

## Documentation

Full documentation available:

- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute quick start guide
- **[HOW_TO_DOWNLOAD.md](HOW_TO_DOWNLOAD.md)** - Comprehensive download guide
- **[TESTING_CHECKLIST.md](TESTING_CHECKLIST.md)** - Complete testing checklist
- **[README.md](README.md)** - Full feature documentation
- **[FALLOUT4_COMPLETE.md](FALLOUT4_COMPLETE.md)** - Fallout 4 advanced features
- **[XEDIT_INTEGRATION.md](XEDIT_INTEGRATION.md)** - xEdit integration guide

---

## Need More Help?

1. Check the documentation files above
2. Run any command with `--help`: `MossyManager.exe auto --help`
3. Enable verbose mode: `MossyManager.exe auto --verbose --profile "Default"`
4. Report issues: https://github.com/POINTYTHRUNDRA654/Mossy-manager./issues

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                    MOSSY MANAGER CHEAT SHEET                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Download: github.com/POINTYTHRUNDRA654/Mossy-manager./    │
│           releases/latest                                   │
│                                                             │
│  Quick Test: MossyManager.exe info                         │
│                                                             │
│  Demo Test:  MossyManager.exe loadorder list \             │
│              --plugins-file demo/profile/plugins.txt        │
│                                                             │
│  Safe Test:  MossyManager.exe fallout4 optimize \          │
│              --profile "Default" --dry-run                  │
│                                                             │
│  Full Auto:  MossyManager.exe auto --profile "Default"     │
│                                                             │
│  Get Help:   MossyManager.exe --help                       │
│              MossyManager.exe COMMAND --help                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

**Ready to optimize your Fallout 4 setup?**

1. [Download Now](https://github.com/POINTYTHRUNDRA654/Mossy-manager./releases/latest)
2. Run: `MossyManager.exe info`
3. Test: `MossyManager.exe auto --profile "Default"`

🎉 That's it! Your game will be optimized and running smoothly!
