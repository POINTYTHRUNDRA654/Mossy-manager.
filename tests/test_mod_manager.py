"""Tests for ModManager"""

import pytest
from pathlib import Path
import tempfile
import os

from mossy_manager.mod_manager import ModManager


class TestModManager:
    """Test ModManager class"""

    def test_manager_creation_with_path(self):
        """Test creating a ModManager with an explicit path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModManager(tmpdir)
            assert manager.mo2_path == tmpdir
            assert manager.mods_path == Path(tmpdir) / "mods"

    def test_manager_creation_without_path(self):
        """Test creating a ModManager without a path (uses cwd)"""
        manager = ModManager()
        assert manager.mods_path == Path(os.getcwd()) / "mods"

    def test_list_mods_empty_directory(self):
        """Test listing mods when the mods directory doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModManager(tmpdir)
            mods = manager.list_mods()
            assert mods == []

    def test_list_mods(self):
        """Test listing mods from a populated mods directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mods_dir = Path(tmpdir) / "mods"
            mods_dir.mkdir()
            (mods_dir / "ModA").mkdir()
            (mods_dir / "ModB").mkdir()
            (mods_dir / "ModC").mkdir()

            manager = ModManager(tmpdir)
            mods = manager.list_mods()

            assert mods == ["ModA", "ModB", "ModC"]

    def test_list_mods_sorted(self):
        """Test that mods are returned in sorted order"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mods_dir = Path(tmpdir) / "mods"
            mods_dir.mkdir()
            (mods_dir / "ZMod").mkdir()
            (mods_dir / "AMod").mkdir()
            (mods_dir / "MMod").mkdir()

            manager = ModManager(tmpdir)
            mods = manager.list_mods()

            assert mods == ["AMod", "MMod", "ZMod"]

    def test_list_mods_ignores_files(self):
        """Test that list_mods only returns directories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mods_dir = Path(tmpdir) / "mods"
            mods_dir.mkdir()
            (mods_dir / "RealMod").mkdir()
            (mods_dir / "notamod.txt").write_text("file")

            manager = ModManager(tmpdir)
            mods = manager.list_mods()

            assert "RealMod" in mods
            assert "notamod.txt" not in mods

    def test_enable_mod(self):
        """Test enabling a mod"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mods_dir = Path(tmpdir) / "mods"
            mods_dir.mkdir()
            (mods_dir / "TestMod").mkdir()

            manager = ModManager(tmpdir)
            result = manager.enable_mod("TestMod")

            assert result is True

    def test_enable_mod_not_found(self):
        """Test enabling a mod that doesn't exist raises ValueError"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModManager(tmpdir)
            with pytest.raises(ValueError, match="not found"):
                manager.enable_mod("NonExistentMod")

    def test_disable_mod(self):
        """Test disabling a mod"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mods_dir = Path(tmpdir) / "mods"
            mods_dir.mkdir()
            (mods_dir / "TestMod").mkdir()

            manager = ModManager(tmpdir)
            result = manager.disable_mod("TestMod")

            assert result is True

    def test_disable_mod_not_found(self):
        """Test disabling a mod that doesn't exist raises ValueError"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModManager(tmpdir)
            with pytest.raises(ValueError, match="not found"):
                manager.disable_mod("NonExistentMod")

    def test_get_mod_info(self):
        """Test getting information about a mod"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mods_dir = Path(tmpdir) / "mods"
            mods_dir.mkdir()
            mod_dir = mods_dir / "TestMod"
            mod_dir.mkdir()
            (mod_dir / "somefile.esp").write_text("data")

            manager = ModManager(tmpdir)
            info = manager.get_mod_info("TestMod")

            assert info["name"] == "TestMod"
            assert info["exists"] is True
            assert info["file_count"] == 1
            assert info["has_meta"] is False

    def test_get_mod_info_with_meta(self):
        """Test getting mod info when meta.ini exists"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mods_dir = Path(tmpdir) / "mods"
            mods_dir.mkdir()
            mod_dir = mods_dir / "TestMod"
            mod_dir.mkdir()
            (mod_dir / "meta.ini").write_text("[General]\nmodid=12345\n")

            manager = ModManager(tmpdir)
            info = manager.get_mod_info("TestMod")

            assert info["has_meta"] is True

    def test_get_mod_info_not_found(self):
        """Test getting info for a non-existent mod raises ValueError"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModManager(tmpdir)
            with pytest.raises(ValueError, match="not found"):
                manager.get_mod_info("NonExistentMod")


class TestModManagerModlist:
    """Tests that enable_mod/disable_mod actually write modlist.txt."""

    def _make_mo2(self, tmpdir, mod_name="TestMod"):
        mods_dir = Path(tmpdir) / "mods"
        mods_dir.mkdir(parents=True, exist_ok=True)
        (mods_dir / mod_name).mkdir()
        return ModManager(tmpdir)

    def test_enable_mod_writes_modlist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = self._make_mo2(tmpdir)
            manager.enable_mod("TestMod", profile_name="Default")
            modlist = (Path(tmpdir) / "profiles" / "Default" / "modlist.txt").read_text()
            assert "+TestMod" in modlist

    def test_disable_mod_writes_modlist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = self._make_mo2(tmpdir)
            manager.disable_mod("TestMod", profile_name="Default")
            modlist = (Path(tmpdir) / "profiles" / "Default" / "modlist.txt").read_text()
            assert "-TestMod" in modlist

    def test_enable_mod_updates_existing_disabled_entry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = self._make_mo2(tmpdir)
            modlist_path = Path(tmpdir) / "profiles" / "Default" / "modlist.txt"
            modlist_path.parent.mkdir(parents=True, exist_ok=True)
            modlist_path.write_text("-TestMod\n")
            manager.enable_mod("TestMod", profile_name="Default")
            content = modlist_path.read_text()
            assert "+TestMod" in content
            assert "-TestMod" not in content

    def test_disable_mod_updates_existing_enabled_entry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = self._make_mo2(tmpdir)
            modlist_path = Path(tmpdir) / "profiles" / "Default" / "modlist.txt"
            modlist_path.parent.mkdir(parents=True, exist_ok=True)
            modlist_path.write_text("+TestMod\n")
            manager.disable_mod("TestMod", profile_name="Default")
            content = modlist_path.read_text()
            assert "-TestMod" in content
            assert "+TestMod" not in content


class TestModManagerGetInfo:
    """Tests that get_mod_info parses meta.ini fields."""

    def test_get_mod_info_parses_nexus_mod_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_dir = Path(tmpdir) / "mods" / "TestMod"
            mod_dir.mkdir(parents=True)
            (mod_dir / "meta.ini").write_text(
                "[General]\nmodid=12345\nversion=1.2.3\n"
            )
            manager = ModManager(tmpdir)
            info = manager.get_mod_info("TestMod")
            assert info["nexus_mod_id"] == "12345"
            assert info["version"] == "1.2.3"

    def test_get_mod_info_no_meta_has_no_nexus_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_dir = Path(tmpdir) / "mods" / "TestMod"
            mod_dir.mkdir(parents=True)
            manager = ModManager(tmpdir)
            info = manager.get_mod_info("TestMod")
            assert info["has_meta"] is False
            assert "nexus_mod_id" not in info


if __name__ == "__main__":
    pytest.main([__file__, "-v"])