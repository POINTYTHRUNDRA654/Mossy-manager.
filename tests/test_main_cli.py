"""Tests for the mossy-manager argparse CLI (main.py)"""

import pytest
import sys
import tempfile
import os
from pathlib import Path
from unittest.mock import patch
from io import StringIO

from mossy_manager.main import main
from click.testing import CliRunner


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


class TestMainCLIDetect:
    """Test the detect sub-command"""

    def test_detect_no_mo2(self, monkeypatch):
        """When MO2 is not installed, user is informed"""
        monkeypatch.setattr(
            'mossy_manager.integrations.mo2.MO2Integration.detect_mo2_installation',
            lambda: None
        )
        rc, out, err = run_main('detect')
        assert rc == 0
        assert 'Mod Organizer 2 installation not detected' in out

    def test_detect_with_mo2_writes_config(self, tmp_path, monkeypatch):
        """MO2 detection should print info and be able to write ini"""
        fake = tmp_path / 'MO2'
        (fake / 'tools' / 'MossyManager').mkdir(parents=True)
        (fake / 'tools' / 'MossyManager' / 'MossyManager.exe').write_text('')
        monkeypatch.setattr(
            'mossy_manager.integrations.mo2.MO2Integration.detect_mo2_installation',
            lambda: fake
        )
        # prevent xEdit detection from printing path
        monkeypatch.setattr(
            'mossy_manager.utils.xedit_integration.XEditIntegration.detect_xedit',
            lambda game, search_roots=None: None
        )
        cfg = tmp_path / 'config.ini'
        rc, out, err = run_main('detect', '--mo2-config', str(cfg))
        assert rc == 0
        # message should mention MO2 path or "MO2 at"
        assert 'MO2 at:' in out or 'Mod Organizer 2' in out
        assert cfg.exists()
        assert 'name=Mossy Manager' in cfg.read_text()

    def test_auto_fo4_uses_active_profile(self, tmp_path, monkeypatch):
        """click CLI: auto-fo4 defaults to active profile when none provided"""
        # prepare fake MO2 directory with profile
        fake = tmp_path / 'MO2'
        (fake / 'profiles' / 'Default').mkdir(parents=True)
        (fake / 'profiles' / 'Default' / 'plugins.txt').write_text('*Fallout4.esm\n')
        (fake / 'profiles' / 'Default' / 'loadorder.txt').write_text('Fallout4.esm\n')
        (fake / 'profiles' / '_active_profile.txt').write_text('Default')
        monkeypatch.setattr(
            'mossy_manager.integrations.mo2.MO2Integration.detect_mo2_installation',
            lambda: fake
        )
        from mossy_manager.games.fallout4 import Fallout4Rules
        monkeypatch.setattr(Fallout4Rules, 'optimize_load_order', lambda order, data_path=None: order)

        from mossy_manager.cli.main import main as click_main
        from click.testing import CliRunner
        r = CliRunner().invoke(click_main, ['loadorder', 'auto-fo4'])
        assert r.exit_code == 0
        assert 'Using active profile: Default' in r.stdout

    def test_auto_fo4_conflict_scan(self, tmp_path, monkeypatch):
        """scan-conflicts option should invoke ConflictResolver"""
        fake = tmp_path / 'MO2'
        (fake / 'profiles' / 'Default').mkdir(parents=True)
        # ensure mods dir exists
        (fake / 'mods').mkdir(parents=True)
        (fake / 'profiles' / 'Default' / 'plugins.txt').write_text('*A.esm\n')
        (fake / 'profiles' / 'Default' / 'loadorder.txt').write_text('A.esm\n')
        (fake / 'profiles' / '_active_profile.txt').write_text('Default')
        monkeypatch.setattr(
            'mossy_manager.integrations.mo2.MO2Integration.detect_mo2_installation',
            lambda: fake
        )
        # stub optimizer
        from mossy_manager.games.fallout4 import Fallout4Rules
        monkeypatch.setattr(Fallout4Rules, 'optimize_load_order', lambda order, data_path=None: order)
        # patch ConflictResolver to produce simple output
        import importlib
        cli_module = importlib.import_module('mossy_manager.cli.main')
        class DummyResolver:
            def __init__(self, mods_path):
                pass
            def scan_mod_files(self, name, path):
                pass
            def generate_report(self):
                return 'dummy report'
            def get_statistics(self):
                return {'total_conflicts':0,'critical':0,'high':0,'medium':0,'low':0}
            def export_for_xedit(self):
                return []
        monkeypatch.setattr(cli_module, 'ConflictResolver', DummyResolver)
        from mossy_manager.cli.main import main as click_main
        from click.testing import CliRunner
        r = CliRunner().invoke(click_main, ['loadorder', 'auto-fo4', '--scan-conflicts'])
        assert r.exit_code == 0
        assert 'dummy report' in r.stdout

    def test_auto_fo4_resolve_xedit(self, tmp_path, monkeypatch):
        """resolve-xedit flag should call XEditIntegration.export_conflicts"""
        fake = tmp_path / 'MO2'
        (fake / 'profiles' / 'Default').mkdir(parents=True)
        (fake / 'mods').mkdir(parents=True)
        (fake / 'profiles' / 'Default' / 'plugins.txt').write_text('*A.esm\n')
        (fake / 'profiles' / 'Default' / 'loadorder.txt').write_text('A.esm\n')
        (fake / 'profiles' / '_active_profile.txt').write_text('Default')
        monkeypatch.setattr(
            'mossy_manager.integrations.mo2.MO2Integration.detect_mo2_installation',
            lambda: fake
        )
        from mossy_manager.games.fallout4 import Fallout4Rules
        monkeypatch.setattr(Fallout4Rules, 'optimize_load_order', lambda order, data_path=None: order)
        # stub ConflictResolver so logging is minimal
        import importlib
        cli_module = importlib.import_module('mossy_manager.cli.main')
        class DummyResolver2:
            def __init__(self, mods_path): pass
            def scan_mod_files(self, a,b): pass
            def generate_report(self): return {}
            def get_statistics(self): return {'total_conflicts':0,'critical':0,'high':0,'medium':0,'low':0}
            def export_for_xedit(self):
                return []
        monkeypatch.setattr(cli_module, 'ConflictResolver', DummyResolver2)
        # capture export call
        from mossy_manager.utils.xedit_integration import XEditIntegration
        called = {}
        def fake_create(self, conflicts, patch_name, output_dir):
            called['yes'] = True
            return {'success': True, 'export_path': 'a', 'script_path': 'b', 'xedit_launched': False}
        monkeypatch.setattr(XEditIntegration, 'create_conflict_resolution_patch', fake_create)
        from mossy_manager.cli.main import main as click_main
        from click.testing import CliRunner
        r = CliRunner().invoke(click_main, ['loadorder', 'auto-fo4', '--resolve-xedit'])
        assert r.exit_code == 0
        assert called.get('yes', False) is True

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
