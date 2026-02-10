#!/usr/bin/env python
"""
Build script for creating Mossy Manager executable
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    """Build the executable using PyInstaller"""
    
    print("=" * 60)
    print("Mossy Manager - Build Script")
    print("=" * 60)
    print()
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"✓ PyInstaller found: {PyInstaller.__version__}")
    except ImportError:
        print("✗ PyInstaller not found")
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller installed")
    
    print()
    
    # Check if spec file exists
    spec_file = Path("MossyManager.spec")
    if not spec_file.exists():
        print(f"✗ Spec file not found: {spec_file}")
        return 1
    
    print(f"✓ Spec file found: {spec_file}")
    print()
    
    # Clean previous build
    print("Cleaning previous build...")
    for dir_name in ['build', 'dist']:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  Removed: {dir_name}/")
    print("✓ Clean complete")
    print()
    
    # Run PyInstaller
    print("Building executable...")
    print("-" * 60)
    
    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        str(spec_file)
    ]
    
    result = subprocess.run(cmd)
    
    print("-" * 60)
    print()
    
    if result.returncode == 0:
        print("✓ Build successful!")
        print()
        
        # Check if executable was created
        exe_path = Path("dist/MossyManager.exe")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"Executable created: {exe_path}")
            print(f"Size: {size_mb:.2f} MB")
            print()
            print("You can now distribute the MossyManager.exe file!")
            print("Users can run it directly without installing Python.")
        else:
            print("⚠ Warning: Executable not found at expected location")
            return 1
    else:
        print("✗ Build failed")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
