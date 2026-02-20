"""Tests for ProfileManager"""

import pytest
from pathlib import Path
import tempfile
import os

from mossy_manager.profile_manager import ProfileManager


class TestProfileManager:
    """Test ProfileManager class"""

    def test_manager_creation_with_path(self):
        """Test creating a ProfileManager with an explicit path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ProfileManager(tmpdir)
            assert manager.mo2_path == tmpdir
            assert manager.profiles_path == Path(tmpdir) / "profiles"

    def test_manager_creation_without_path(self):
        """Test creating a ProfileManager without a path (uses cwd)"""
        manager = ProfileManager()
        assert manager.profiles_path == Path(os.getcwd()) / "profiles"

    def test_list_profiles_empty(self):
        """Test listing profiles when profiles directory doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ProfileManager(tmpdir)
            profiles = manager.list_profiles()
            assert profiles == []

    def test_list_profiles(self):
        """Test listing profiles from a populated profiles directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            profiles_dir = Path(tmpdir) / "profiles"
            profiles_dir.mkdir()
            (profiles_dir / "Default").mkdir()
            (profiles_dir / "Hardcore").mkdir()

            manager = ProfileManager(tmpdir)
            profiles = manager.list_profiles()

            assert "Default" in profiles
            assert "Hardcore" in profiles

    def test_list_profiles_sorted(self):
        """Test that profiles are returned in sorted order"""
        with tempfile.TemporaryDirectory() as tmpdir:
            profiles_dir = Path(tmpdir) / "profiles"
            profiles_dir.mkdir()
            (profiles_dir / "ZProfile").mkdir()
            (profiles_dir / "AProfile").mkdir()

            manager = ProfileManager(tmpdir)
            profiles = manager.list_profiles()

            assert profiles == ["AProfile", "ZProfile"]

    def test_list_profiles_ignores_files(self):
        """Test that list_profiles only returns directories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            profiles_dir = Path(tmpdir) / "profiles"
            profiles_dir.mkdir()
            (profiles_dir / "RealProfile").mkdir()
            (profiles_dir / "notaprofile.txt").write_text("file")

            manager = ProfileManager(tmpdir)
            profiles = manager.list_profiles()

            assert "RealProfile" in profiles
            assert "notaprofile.txt" not in profiles

    def test_create_profile(self):
        """Test creating a new profile"""
        with tempfile.TemporaryDirectory() as tmpdir:
            profiles_dir = Path(tmpdir) / "profiles"
            profiles_dir.mkdir()

            manager = ProfileManager(tmpdir)
            result = manager.create_profile("NewProfile")

            assert result is True
            assert (profiles_dir / "NewProfile").exists()
            assert (profiles_dir / "NewProfile" / "modlist.txt").exists()

    def test_create_profile_creates_modlist(self):
        """Test that create_profile creates a modlist.txt"""
        with tempfile.TemporaryDirectory() as tmpdir:
            profiles_dir = Path(tmpdir) / "profiles"
            profiles_dir.mkdir()

            manager = ProfileManager(tmpdir)
            manager.create_profile("TestProfile")

            modlist = (profiles_dir / "TestProfile" / "modlist.txt").read_text()
            assert "TestProfile" in modlist

    def test_create_profile_already_exists(self):
        """Test that creating an existing profile raises ValueError"""
        with tempfile.TemporaryDirectory() as tmpdir:
            profiles_dir = Path(tmpdir) / "profiles"
            profiles_dir.mkdir()
            (profiles_dir / "ExistingProfile").mkdir()

            manager = ProfileManager(tmpdir)
            with pytest.raises(ValueError, match="already exists"):
                manager.create_profile("ExistingProfile")

    def test_delete_profile(self):
        """Test deleting a profile"""
        with tempfile.TemporaryDirectory() as tmpdir:
            profiles_dir = Path(tmpdir) / "profiles"
            profiles_dir.mkdir()
            (profiles_dir / "ToDelete").mkdir()

            manager = ProfileManager(tmpdir)
            result = manager.delete_profile("ToDelete")

            assert result is True
            assert not (profiles_dir / "ToDelete").exists()

    def test_delete_profile_not_found(self):
        """Test that deleting a non-existent profile raises ValueError"""
        with tempfile.TemporaryDirectory() as tmpdir:
            profiles_dir = Path(tmpdir) / "profiles"
            profiles_dir.mkdir()

            manager = ProfileManager(tmpdir)
            with pytest.raises(ValueError, match="not found"):
                manager.delete_profile("NonExistent")

    def test_switch_profile(self):
        """Test switching to a profile"""
        with tempfile.TemporaryDirectory() as tmpdir:
            profiles_dir = Path(tmpdir) / "profiles"
            profiles_dir.mkdir()
            (profiles_dir / "TargetProfile").mkdir()

            manager = ProfileManager(tmpdir)
            result = manager.switch_profile("TargetProfile")

            assert result is True

    def test_switch_profile_not_found(self):
        """Test that switching to a non-existent profile raises ValueError"""
        with tempfile.TemporaryDirectory() as tmpdir:
            profiles_dir = Path(tmpdir) / "profiles"
            profiles_dir.mkdir()

            manager = ProfileManager(tmpdir)
            with pytest.raises(ValueError, match="not found"):
                manager.switch_profile("NonExistent")

    def test_get_profile_info(self):
        """Test getting profile information"""
        with tempfile.TemporaryDirectory() as tmpdir:
            profiles_dir = Path(tmpdir) / "profiles"
            profiles_dir.mkdir()
            profile_dir = profiles_dir / "TestProfile"
            profile_dir.mkdir()
            (profile_dir / "modlist.txt").write_text("# modlist\n")

            manager = ProfileManager(tmpdir)
            info = manager.get_profile_info("TestProfile")

            assert info["name"] == "TestProfile"
            assert info["exists"] is True
            assert info["has_modlist"] is True

    def test_get_profile_info_no_modlist(self):
        """Test getting profile info when modlist.txt is absent"""
        with tempfile.TemporaryDirectory() as tmpdir:
            profiles_dir = Path(tmpdir) / "profiles"
            profiles_dir.mkdir()
            (profiles_dir / "BareProfile").mkdir()

            manager = ProfileManager(tmpdir)
            info = manager.get_profile_info("BareProfile")

            assert info["has_modlist"] is False

    def test_get_profile_info_not_found(self):
        """Test that getting info for a non-existent profile raises ValueError"""
        with tempfile.TemporaryDirectory() as tmpdir:
            profiles_dir = Path(tmpdir) / "profiles"
            profiles_dir.mkdir()

            manager = ProfileManager(tmpdir)
            with pytest.raises(ValueError, match="not found"):
                manager.get_profile_info("NonExistent")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
