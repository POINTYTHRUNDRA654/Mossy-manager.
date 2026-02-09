#!/usr/bin/env python3
"""
Demo script for Mossy Manager
Creates a test MO2 structure and demonstrates functionality
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import json

def create_test_mo2_structure():
    """Create a test MO2 directory structure"""
    print("Creating test MO2 structure...")
    
    # Create temporary directory
    test_dir = Path(tempfile.gettempdir()) / "mossy_manager_demo"
    
    # Remove if exists
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    test_dir.mkdir()
    
    # Create MO2 structure
    mo2_dir = test_dir / "ModOrganizer2"
    mo2_dir.mkdir()
    
    # Create fake MO2 executable
    mo2_exe = mo2_dir / "ModOrganizer.exe"
    mo2_exe.touch()
    
    # Create mods directory
    mods_dir = mo2_dir / "mods"
    mods_dir.mkdir()
    
    # Create sample mods
    sample_mods = [
        "SkyUI",
        "Unofficial Skyrim Patch",
        "Enhanced Lights and FX",
        "Static Mesh Improvement Mod",
        "JContainers",
        "RaceMenu",
        "Better Dialogue Controls",
        "Better MessageBox Controls"
    ]
    
    for mod_name in sample_mods:
        mod_dir = mods_dir / mod_name
        mod_dir.mkdir()
        
        # Create some fake files in each mod
        (mod_dir / "readme.txt").write_text(f"This is {mod_name}")
        (mod_dir / "mod.esp").touch()
    
    print(f"✓ Test MO2 structure created at: {mo2_dir}")
    print(f"✓ Created {len(sample_mods)} sample mods")
    print()
    
    return mo2_dir


def demonstrate_settings():
    """Demonstrate settings operations"""
    print("=" * 70)
    print("Settings Operations Demo")
    print("=" * 70)
    
    # Create a test settings file
    config_dir = Path(tempfile.gettempdir()) / "mossy_manager_demo" / ".mossy_manager"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.json"
    
    # Create settings
    settings = {
        'mo2_path': '/path/to/ModOrganizer2',
        'auto_launch': False,
        'theme': 'Light'
    }
    
    # Save settings
    with open(config_file, 'w') as f:
        json.dump(settings, f, indent=2)
    
    print(f"✓ Created settings file: {config_file}")
    print(f"✓ Settings content:")
    print(json.dumps(settings, indent=2))
    print()
    
    # Load settings
    with open(config_file, 'r') as f:
        loaded_settings = json.load(f)
    
    print("✓ Settings loaded successfully")
    print(f"  - MO2 Path: {loaded_settings['mo2_path']}")
    print(f"  - Auto Launch: {loaded_settings['auto_launch']}")
    print(f"  - Theme: {loaded_settings['theme']}")
    print()


def demonstrate_mod_discovery(mo2_dir):
    """Demonstrate mod discovery"""
    print("=" * 70)
    print("Mod Discovery Demo")
    print("=" * 70)
    
    mods_dir = mo2_dir / "mods"
    
    if not mods_dir.exists():
        print("✗ Mods directory not found!")
        return
    
    print(f"✓ Scanning mods directory: {mods_dir}")
    print()
    
    # Discover mods
    mods = sorted([d.name for d in mods_dir.iterdir() if d.is_dir()])
    
    print(f"✓ Found {len(mods)} mods:")
    for i, mod in enumerate(mods, 1):
        print(f"  {i}. {mod}")
    print()


def demonstrate_path_validation(mo2_dir):
    """Demonstrate path validation"""
    print("=" * 70)
    print("Path Validation Demo")
    print("=" * 70)
    
    # Check MO2 executable
    mo2_exe = mo2_dir / "ModOrganizer.exe"
    
    if mo2_exe.exists():
        print(f"✓ ModOrganizer.exe found at: {mo2_exe}")
    else:
        print(f"✗ ModOrganizer.exe NOT found at: {mo2_exe}")
    
    # Check mods directory
    mods_dir = mo2_dir / "mods"
    
    if mods_dir.exists() and mods_dir.is_dir():
        print(f"✓ Mods directory found at: {mods_dir}")
    else:
        print(f"✗ Mods directory NOT found at: {mods_dir}")
    
    print()


def run_basic_tests():
    """Run basic functionality tests"""
    print("=" * 70)
    print("Basic Functionality Tests")
    print("=" * 70)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: JSON operations
    try:
        test_data = {'test': 'value'}
        test_json = json.dumps(test_data)
        loaded_data = json.loads(test_json)
        assert loaded_data == test_data
        print("✓ Test 1: JSON operations - PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"✗ Test 1: JSON operations - FAILED: {e}")
        tests_failed += 1
    
    # Test 2: Path operations
    try:
        test_path = Path(tempfile.gettempdir()) / "test"
        test_path.mkdir(exist_ok=True)
        assert test_path.exists()
        shutil.rmtree(test_path)
        print("✓ Test 2: Path operations - PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"✗ Test 2: Path operations - FAILED: {e}")
        tests_failed += 1
    
    # Test 3: Platform detection
    try:
        import platform
        system = platform.system()
        assert system in ['Windows', 'Darwin', 'Linux']
        print(f"✓ Test 3: Platform detection ({system}) - PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"✗ Test 3: Platform detection - FAILED: {e}")
        tests_failed += 1
    
    print()
    print(f"Results: {tests_passed} passed, {tests_failed} failed")
    print()


def print_usage_instructions(mo2_dir):
    """Print instructions for using the test structure"""
    print("=" * 70)
    print("Usage Instructions")
    print("=" * 70)
    print()
    print("To test Mossy Manager with this demo structure:")
    print()
    print("1. Launch Mossy Manager:")
    print("   python3 mossy_manager.py")
    print()
    print("2. Click 'Browse...' and select this path:")
    print(f"   {mo2_dir}")
    print()
    print("3. Click 'Refresh Mods' to see the sample mods")
    print()
    print("4. The demo structure will remain until you delete it:")
    print(f"   rm -rf {mo2_dir.parent}")
    print()
    print("=" * 70)


def main():
    """Main demo function"""
    print()
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "  Mossy Manager - Demo & Test Script".center(68) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print()
    
    # Run basic tests first
    run_basic_tests()
    
    # Create test structure
    mo2_dir = create_test_mo2_structure()
    
    # Demonstrate functionality
    demonstrate_settings()
    demonstrate_path_validation(mo2_dir)
    demonstrate_mod_discovery(mo2_dir)
    
    # Print usage instructions
    print_usage_instructions(mo2_dir)
    
    print()
    print("Demo completed successfully! ✓")
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError during demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
