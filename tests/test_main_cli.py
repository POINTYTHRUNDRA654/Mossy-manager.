"""Tests for the mossy-manager argparse CLI (main.py)"""

import pytest
import sys
import tempfile
import os
from pathlib import Path
from unittest.mock import patch
from io import StringIO

from mossy_manager.main import main


def run_main(*args):
    """Helper: invoke main() with given args, capture stdout/stderr."""
    with patch("sys.argv", ["mossy-manager"] + list(args)):
        captured_out = StringIO()
        captured_err = StringIO()
        with patch("sys.stdout", captured_out), patch("sys.stderr", captured_err):
            try:
                rc = main()
            except SystemExit as e:
                rc = e.code
        return rc, captured_out.getvalue(), captured_err.getvalue()


class TestMainCLINoCommand:
    """Test calling mossy-manager with no sub-command"""

    def test_no_command_prints_help(self):
        """Calling with no args should print help and return 0"""
        with patch("sys.argv", ["mossy-manager"]):
            captured = StringIO()
            with patch("sys.stdout", captured):
                try:
                    rc = main()
                except SystemExit as e:
                    rc = e.code
        assert rc == 0


class TestMainCLIInfo:
    """Test the info sub-command"""

    def test_info_no_path(self):
        rc, out, err = run_main("info")
        assert rc == 0
        assert "Not specified" in out

    def test_info_with_path(self):
        rc, out, err = run_main("info", "--path", "/some/path")
        assert rc == 0
        assert "/some/path" in out


class TestMainCLIMod:
    """Test the mod sub-command"""

    def test_mod_list_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc, out, err = run_main("mod", "list", "--path", tmpdir)
        assert rc == 0
        assert "No mods found" in out

    def test_mod_list_with_mods(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mods_dir = Path(tmpdir) / "mods"
            mods_dir.mkdir()
            (mods_dir / "MyMod").mkdir()
            rc, out, err = run_main("mod", "list", "--path", tmpdir)
        assert rc == 0
        assert "MyMod" in out

    def test_mod_enable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "mods" / "TestMod").mkdir(parents=True)
            rc, out, err = run_main("mod", "enable", "--path", tmpdir, "--name", "TestMod")
        assert rc == 0
        assert "TestMod" in out

    def test_mod_enable_missing_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc, out, err = run_main("mod", "enable", "--path", tmpdir)
        assert rc == 1

    def test_mod_disable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "mods" / "TestMod").mkdir(parents=True)
            rc, out, err = run_main("mod", "disable", "--path", tmpdir, "--name", "TestMod")
        assert rc == 0
        assert "TestMod" in out

    def test_mod_disable_missing_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc, out, err = run_main("mod", "disable", "--path", tmpdir)
        assert rc == 1

    def test_mod_info(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "mods" / "TestMod").mkdir(parents=True)
            rc, out, err = run_main("mod", "info", "--path", tmpdir, "--name", "TestMod")
        assert rc == 0
        assert "TestMod" in out

    def test_mod_info_missing_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc, out, err = run_main("mod", "info", "--path", tmpdir)
        assert rc == 1

    def test_mod_error_handled(self):
        """Accessing a non-existent mod should return rc=1 via exception handler"""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "mods").mkdir()
            rc, out, err = run_main("mod", "info", "--path", tmpdir, "--name", "Ghost")
        assert rc == 1


class TestMainCLIProfile:
    """Test the profile sub-command"""

    def test_profile_list_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc, out, err = run_main("profile", "list", "--path", tmpdir)
        assert rc == 0
        assert "No profiles found" in out

    def test_profile_list_with_profiles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "profiles" / "Default").mkdir(parents=True)
            rc, out, err = run_main("profile", "list", "--path", tmpdir)
        assert rc == 0
        assert "Default" in out

    def test_profile_create(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "profiles").mkdir()
            rc, out, err = run_main("profile", "create", "--path", tmpdir, "--name", "NewProfile")
        assert rc == 0
        assert "NewProfile" in out

    def test_profile_create_missing_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc, out, err = run_main("profile", "create", "--path", tmpdir)
        assert rc == 1

    def test_profile_delete(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "profiles" / "ToDelete").mkdir(parents=True)
            rc, out, err = run_main("profile", "delete", "--path", tmpdir, "--name", "ToDelete")
        assert rc == 0

    def test_profile_delete_missing_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc, out, err = run_main("profile", "delete", "--path", tmpdir)
        assert rc == 1

    def test_profile_switch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "profiles" / "Target").mkdir(parents=True)
            rc, out, err = run_main("profile", "switch", "--path", tmpdir, "--name", "Target")
        assert rc == 0

    def test_profile_switch_missing_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc, out, err = run_main("profile", "switch", "--path", tmpdir)
        assert rc == 1


class TestMainCLIConfig:
    """Test the config sub-command"""

    def test_config_show(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_file = Path(tmpdir) / "config.ini"
            with patch("mossy_manager.config_manager.Path.home", return_value=Path(tmpdir)):
                rc, out, err = run_main("config", "show")
        assert rc == 0

    def test_config_set(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("mossy_manager.config_manager.Path.home", return_value=Path(tmpdir)):
                rc, out, err = run_main("config", "set", "--key", "mo2_path", "--value", "/path/to/mo2")
        assert rc == 0
        assert "mo2_path" in out

    def test_config_set_missing_key(self):
        rc, out, err = run_main("config", "set", "--value", "something")
        assert rc == 1

    def test_config_get(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("mossy_manager.config_manager.Path.home", return_value=Path(tmpdir)):
                # Set a value first, then get it
                run_main("config", "set", "--key", "mo2_path", "--value", "/test/path")
                rc, out, err = run_main("config", "get", "--key", "mo2_path")
        assert rc == 0

    def test_config_get_missing_key_arg(self):
        rc, out, err = run_main("config", "get")
        assert rc == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
