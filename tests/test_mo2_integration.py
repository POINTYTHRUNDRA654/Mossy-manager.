"""Tests for MO2 Integration"""

import pytest
from pathlib import Path
import tempfile
import os

from mossy_manager.integrations.mo2 import MO2Integration


class TestMO2Integration:
    """Test MO2Integration class"""

    def test_creation_no_path(self):
        """Test creating MO2Integration without a path"""
        mo2 = MO2Integration()
        assert mo2.mo2_path is None
        assert mo2.profiles_path is None
        assert mo2.mods_path is None

    def test_creation_with_nonexistent_path(self):
        """Test creating MO2Integration with a path that doesn't exist"""
        mo2 = MO2Integration(Path("/nonexistent/path"))
        assert mo2.profiles_path is None

    def test_creation_with_valid_path(self):
        """Test creating MO2Integration with a valid directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mo2 = MO2Integration(Path(tmpdir))
            assert mo2.profiles_path == Path(tmpdir) / "profiles"
            assert mo2.mods_path == Path(tmpdir) / "mods"

    def test_list_profiles_empty(self):
        """Test listing profiles when none exist"""
        mo2 = MO2Integration()
        profiles = mo2.list_profiles()
        assert profiles == []

    def test_list_profiles(self):
        """Test listing profiles from a directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mo2 = MO2Integration(Path(tmpdir))
            profiles_dir = Path(tmpdir) / "profiles"
            profiles_dir.mkdir()
            (profiles_dir / "Default").mkdir()
            (profiles_dir / "Hardcore").mkdir()

            profiles = mo2.list_profiles()
            assert "Default" in profiles
            assert "Hardcore" in profiles

    def test_get_profile_path_exists(self):
        """Test getting path to an existing profile"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mo2 = MO2Integration(Path(tmpdir))
            profiles_dir = Path(tmpdir) / "profiles"
            profiles_dir.mkdir()
            (profiles_dir / "Default").mkdir()

            path = mo2.get_profile_path("Default")
            assert path == profiles_dir / "Default"

    def test_get_profile_path_missing(self):
        """Test getting path to a non-existent profile returns None"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mo2 = MO2Integration(Path(tmpdir))
            (Path(tmpdir) / "profiles").mkdir()
            path = mo2.get_profile_path("NonExistent")
            assert path is None

    def test_get_profile_path_no_profiles_path(self):
        """Test get_profile_path when profiles_path is not set returns None"""
        mo2 = MO2Integration()
        assert mo2.get_profile_path("Default") is None

    def test_read_plugins_txt(self):
        """Test reading plugins.txt from a profile"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mo2 = MO2Integration(Path(tmpdir))
            profile_dir = Path(tmpdir) / "profiles" / "Default"
            profile_dir.mkdir(parents=True)
            plugins_file = profile_dir / "plugins.txt"
            plugins_file.write_text(
                "# Comment\n*Fallout4.esm\n*DLCRobot.esm\nDisabledMod.esp\n"
            )

            plugins = mo2.read_plugins_txt("Default")

            assert plugins["Fallout4.esm"] is True
            assert plugins["DLCRobot.esm"] is True
            assert plugins["DisabledMod.esp"] is False

    def test_read_plugins_txt_missing_profile(self):
        """Test reading plugins.txt for a missing profile returns empty dict"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mo2 = MO2Integration(Path(tmpdir))
            (Path(tmpdir) / "profiles").mkdir()
            result = mo2.read_plugins_txt("NonExistent")
            assert result == {}

    def test_read_loadorder_txt(self):
        """Test reading loadorder.txt from a profile"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mo2 = MO2Integration(Path(tmpdir))
            profile_dir = Path(tmpdir) / "profiles" / "Default"
            profile_dir.mkdir(parents=True)
            lo_file = profile_dir / "loadorder.txt"
            lo_file.write_text("# Comment\nFallout4.esm\nDLCRobot.esm\nMyMod.esp\n")

            order = mo2.read_loadorder_txt("Default")

            assert order == ["Fallout4.esm", "DLCRobot.esm", "MyMod.esp"]

    def test_read_loadorder_txt_missing_profile(self):
        """Test reading loadorder.txt for a missing profile returns empty list"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mo2 = MO2Integration(Path(tmpdir))
            (Path(tmpdir) / "profiles").mkdir()
            result = mo2.read_loadorder_txt("NonExistent")
            assert result == []

    def test_write_plugins_txt(self):
        """Test writing plugins.txt to a profile"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mo2 = MO2Integration(Path(tmpdir))
            profile_dir = Path(tmpdir) / "profiles" / "Default"
            profile_dir.mkdir(parents=True)

            plugins = {"Fallout4.esm": True, "DLCRobot.esm": True, "DisabledMod.esp": False}
            result = mo2.write_plugins_txt("Default", plugins)

            assert result is True
            content = (profile_dir / "plugins.txt").read_text()
            assert "*Fallout4.esm" in content
            assert "*DLCRobot.esm" in content
            assert "DisabledMod.esp" in content
            assert "*DisabledMod.esp" not in content

    def test_write_plugins_txt_missing_profile(self):
        """Test writing plugins.txt for a missing profile returns False"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mo2 = MO2Integration(Path(tmpdir))
            (Path(tmpdir) / "profiles").mkdir()
            result = mo2.write_plugins_txt("NonExistent", {})
            assert result is False

    def test_write_loadorder_txt(self):
        """Test writing loadorder.txt to a profile"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mo2 = MO2Integration(Path(tmpdir))
            profile_dir = Path(tmpdir) / "profiles" / "Default"
            profile_dir.mkdir(parents=True)

            load_order = ["Fallout4.esm", "DLCRobot.esm", "MyMod.esp"]
            result = mo2.write_loadorder_txt("Default", load_order)

            assert result is True
            content = (profile_dir / "loadorder.txt").read_text()
            assert "Fallout4.esm" in content
            assert "MyMod.esp" in content

    def test_write_loadorder_txt_missing_profile(self):
        """Test writing loadorder.txt for a missing profile returns False"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mo2 = MO2Integration(Path(tmpdir))
            (Path(tmpdir) / "profiles").mkdir()
            result = mo2.write_loadorder_txt("NonExistent", [])
            assert result is False

    def test_read_modlist_txt(self):
        """Test reading modlist.txt from a profile"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mo2 = MO2Integration(Path(tmpdir))
            profile_dir = Path(tmpdir) / "profiles" / "Default"
            profile_dir.mkdir(parents=True)
            modlist_file = profile_dir / "modlist.txt"
            modlist_file.write_text("+EnabledMod\n-DisabledMod\n# Comment\n")

            mods = mo2.read_modlist_txt("Default")

            assert mods["EnabledMod"] is True
            assert mods["DisabledMod"] is False

    def test_read_modlist_txt_missing(self):
        """Test reading modlist.txt when it doesn't exist returns empty dict"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mo2 = MO2Integration(Path(tmpdir))
            profile_dir = Path(tmpdir) / "profiles" / "Default"
            profile_dir.mkdir(parents=True)

            result = mo2.read_modlist_txt("Default")
            assert result == {}

    def test_roundtrip_plugins(self):
        """Test write then read produces identical results"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mo2 = MO2Integration(Path(tmpdir))
            profile_dir = Path(tmpdir) / "profiles" / "Default"
            profile_dir.mkdir(parents=True)

            original = {"Fallout4.esm": True, "DLCRobot.esm": True, "Mod.esp": False}
            mo2.write_plugins_txt("Default", original)
            read_back = mo2.read_plugins_txt("Default")

            assert read_back == original

    def test_roundtrip_loadorder(self):
        """Test write then read load order produces identical results"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mo2 = MO2Integration(Path(tmpdir))
            profile_dir = Path(tmpdir) / "profiles" / "Default"
            profile_dir.mkdir(parents=True)

            original = ["Fallout4.esm", "DLCRobot.esm", "MyMod.esp"]
            mo2.write_loadorder_txt("Default", original)
            read_back = mo2.read_loadorder_txt("Default")

            assert read_back == original

    def test_get_mo2_info(self):
        """Test get_mo2_info returns expected structure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mo2 = MO2Integration(Path(tmpdir))
            (Path(tmpdir) / "profiles").mkdir()

            info = mo2.get_mo2_info()

            assert "mo2_path" in info
            assert "profiles" in info
            assert "detected" in info
            assert info["detected"] is True

    def test_get_mo2_info_no_path(self):
        """Test get_mo2_info when not initialised"""
        mo2 = MO2Integration()
        info = mo2.get_mo2_info()
        assert info["detected"] is False
        assert info["mo2_path"] is None


    def test_detect_game_instance_returns_mo2_path(self):
        """detect_game_instance returns mo2_path when no portable instance exists"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mo2 = MO2Integration(Path(tmpdir))
            result = mo2.detect_game_instance("Fallout4")
            assert result == Path(tmpdir)

    def test_detect_game_instance_portable(self):
        """detect_game_instance returns portable path when it exists"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a 'Fallout4' sub-directory to simulate a portable instance
            (Path(tmpdir) / "Fallout4").mkdir()
            mo2 = MO2Integration(Path(tmpdir))
            result = mo2.detect_game_instance("Fallout4")
            assert result == Path(tmpdir) / "Fallout4"

    def test_detect_game_instance_no_mo2_path(self):
        """detect_game_instance when mo2_path is None and auto-detect fails"""
        mo2 = MO2Integration()
        # Patch detect_mo2_installation to return None so no side-effects occur
        from unittest.mock import patch
        with patch.object(type(mo2), "detect_mo2_installation", return_value=None):
            result = mo2.detect_game_instance("Fallout4")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
