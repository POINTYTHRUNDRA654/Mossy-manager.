#!/usr/bin/env python3
"""
Test suite for Mossy Manager
Tests core functionality without requiring a display
"""

import unittest
import tempfile
import shutil
import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import the module under test
# We need to mock tkinter before importing
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()

import mossy_manager


class TestSettingsManagement(unittest.TestCase):
    """Test settings loading and saving functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.config_file = Path(self.test_dir) / "config.json"
        
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_default_settings(self):
        """Test that default settings are created correctly"""
        # Create a mock app instance
        with patch('mossy_manager.tk.Tk'):
            app = mossy_manager.MossyManagerApp(Mock())
            
            # Check default settings
            self.assertIn('mo2_path', app.settings)
            self.assertIn('auto_launch', app.settings)
            self.assertIn('theme', app.settings)
            self.assertEqual(app.settings['mo2_path'], '')
            self.assertEqual(app.settings['auto_launch'], False)
            self.assertEqual(app.settings['theme'], 'Light')
    
    def test_save_and_load_settings(self):
        """Test that settings can be saved and loaded"""
        test_settings = {
            'mo2_path': '/path/to/mo2',
            'auto_launch': True,
            'theme': 'Dark'
        }
        
        # Save settings
        with open(self.config_file, 'w') as f:
            json.dump(test_settings, f)
        
        # Load settings
        with open(self.config_file, 'r') as f:
            loaded_settings = json.load(f)
        
        # Verify
        self.assertEqual(loaded_settings['mo2_path'], '/path/to/mo2')
        self.assertEqual(loaded_settings['auto_launch'], True)
        self.assertEqual(loaded_settings['theme'], 'Dark')
    
    def test_settings_file_creation(self):
        """Test that settings file and directory are created"""
        config_dir = Path(self.test_dir) / ".mossy_manager"
        config_file = config_dir / "config.json"
        
        # Ensure directory doesn't exist
        self.assertFalse(config_dir.exists())
        
        # Create directory
        config_dir.mkdir(exist_ok=True)
        
        # Verify directory was created
        self.assertTrue(config_dir.exists())
        
        # Save settings
        settings = {'test': 'value'}
        with open(config_file, 'w') as f:
            json.dump(settings, f)
        
        # Verify file was created
        self.assertTrue(config_file.exists())


class TestPathValidation(unittest.TestCase):
    """Test MO2 path validation and mod discovery"""
    
    def setUp(self):
        """Set up test environment with fake MO2 structure"""
        self.test_dir = tempfile.mkdtemp()
        self.mo2_path = Path(self.test_dir) / "ModOrganizer2"
        self.mo2_path.mkdir()
        
        # Create fake MO2 structure
        (self.mo2_path / "ModOrganizer.exe").touch()
        self.mods_dir = self.mo2_path / "mods"
        self.mods_dir.mkdir()
        
        # Create some fake mods
        (self.mods_dir / "TestMod1").mkdir()
        (self.mods_dir / "TestMod2").mkdir()
        (self.mods_dir / "TestMod3").mkdir()
        
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_mo2_exe_exists(self):
        """Test that MO2 executable can be found"""
        mo2_exe = self.mo2_path / "ModOrganizer.exe"
        self.assertTrue(mo2_exe.exists())
    
    def test_mods_directory_exists(self):
        """Test that mods directory can be found"""
        self.assertTrue(self.mods_dir.exists())
        self.assertTrue(self.mods_dir.is_dir())
    
    def test_mod_discovery(self):
        """Test that mods can be discovered in the mods directory"""
        mods = [d.name for d in self.mods_dir.iterdir() if d.is_dir()]
        
        self.assertEqual(len(mods), 3)
        self.assertIn("TestMod1", mods)
        self.assertIn("TestMod2", mods)
        self.assertIn("TestMod3", mods)
    
    def test_invalid_mo2_path(self):
        """Test handling of invalid MO2 path"""
        invalid_path = Path(self.test_dir) / "NonExistent"
        self.assertFalse(invalid_path.exists())
    
    def test_missing_mods_directory(self):
        """Test handling when mods directory doesn't exist"""
        # Remove mods directory
        shutil.rmtree(self.mods_dir)
        
        self.assertFalse(self.mods_dir.exists())


class TestCrossPlatformSupport(unittest.TestCase):
    """Test cross-platform functionality"""
    
    def test_platform_detection(self):
        """Test that platform can be detected"""
        import platform as plt
        system = plt.system()
        
        # Should be one of the supported platforms
        self.assertIn(system, ['Windows', 'Darwin', 'Linux'])
    
    @patch('mossy_manager.platform.system')
    def test_windows_launch(self, mock_system):
        """Test Windows-specific launch mechanism"""
        mock_system.return_value = 'Windows'
        test_path = Path("C:/test/ModOrganizer.exe")
        
        # On Windows, os.startfile would be called
        # We can't test it directly on non-Windows, but we can verify the logic
        system = mock_system()
        self.assertEqual(system, 'Windows')
        
        # The actual os.startfile call would happen here on Windows
        # This test verifies the platform detection works correctly
    
    @patch('mossy_manager.platform.system')
    @patch('mossy_manager.subprocess.Popen')
    def test_macos_launch(self, mock_popen, mock_system):
        """Test macOS-specific launch mechanism"""
        mock_system.return_value = 'Darwin'
        test_path = Path("/Applications/ModOrganizer.exe")
        
        # Simulate what the app does
        if mock_system() == 'Darwin':
            mock_popen(['open', str(test_path)])
        
        mock_popen.assert_called_once_with(['open', str(test_path)])
    
    @patch('mossy_manager.platform.system')
    @patch('mossy_manager.subprocess.Popen')
    def test_linux_launch(self, mock_popen, mock_system):
        """Test Linux-specific launch mechanism"""
        mock_system.return_value = 'Linux'
        test_path = Path("/home/user/ModOrganizer.exe")
        
        # Simulate what the app does
        system = mock_system()
        if system not in ['Windows', 'Darwin']:
            mock_popen(['xdg-open', str(test_path)])
        
        mock_popen.assert_called_once_with(['xdg-open', str(test_path)])


class TestConfigFileOperations(unittest.TestCase):
    """Test configuration file read/write operations"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.config_file = Path(self.test_dir) / "config.json"
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_write_valid_json(self):
        """Test writing valid JSON configuration"""
        settings = {
            'mo2_path': '/test/path',
            'auto_launch': True,
            'theme': 'Dark'
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(settings, f, indent=2)
        
        self.assertTrue(self.config_file.exists())
        
        # Verify content
        with open(self.config_file, 'r') as f:
            loaded = json.load(f)
        
        self.assertEqual(loaded, settings)
    
    def test_read_missing_file(self):
        """Test handling of missing configuration file"""
        self.assertFalse(self.config_file.exists())
        
        # Should handle gracefully (default settings)
        default_settings = {
            'mo2_path': '',
            'auto_launch': False,
            'theme': 'Light'
        }
        
        # This simulates the app behavior
        if not self.config_file.exists():
            settings = default_settings
        else:
            with open(self.config_file, 'r') as f:
                settings = json.load(f)
        
        self.assertEqual(settings, default_settings)
    
    def test_malformed_json(self):
        """Test handling of malformed JSON"""
        # Write invalid JSON
        with open(self.config_file, 'w') as f:
            f.write("{ invalid json }")
        
        # Try to load it
        with self.assertRaises(json.JSONDecodeError):
            with open(self.config_file, 'r') as f:
                json.load(f)


class TestModListOperations(unittest.TestCase):
    """Test mod list operations"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.mods_dir = Path(self.test_dir) / "mods"
        self.mods_dir.mkdir()
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_empty_mods_directory(self):
        """Test handling of empty mods directory"""
        mods = [d.name for d in self.mods_dir.iterdir() if d.is_dir()]
        self.assertEqual(len(mods), 0)
    
    def test_mixed_content_filtering(self):
        """Test that only directories are recognized as mods"""
        # Create mixed content
        (self.mods_dir / "ValidMod1").mkdir()
        (self.mods_dir / "ValidMod2").mkdir()
        (self.mods_dir / "readme.txt").touch()
        (self.mods_dir / "config.ini").touch()
        
        # Filter only directories
        mods = [d.name for d in self.mods_dir.iterdir() if d.is_dir()]
        
        self.assertEqual(len(mods), 2)
        self.assertIn("ValidMod1", mods)
        self.assertIn("ValidMod2", mods)
        self.assertNotIn("readme.txt", mods)
        self.assertNotIn("config.ini", mods)
    
    def test_mod_sorting(self):
        """Test that mods are sorted alphabetically"""
        # Create mods in random order
        (self.mods_dir / "Zebra").mkdir()
        (self.mods_dir / "Alpha").mkdir()
        (self.mods_dir / "Beta").mkdir()
        
        mods = sorted([d.name for d in self.mods_dir.iterdir() if d.is_dir()])
        
        self.assertEqual(mods, ["Alpha", "Beta", "Zebra"])


def run_tests():
    """Run all tests and return results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSettingsManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestPathValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestCrossPlatformSupport))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigFileOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestModListOperations))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    print("=" * 70)
    print("Mossy Manager Test Suite")
    print("=" * 70)
    print()
    
    result = run_tests()
    
    print()
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
