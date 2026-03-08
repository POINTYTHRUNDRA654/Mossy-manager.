"""Tests for the mossy Click CLI (cli/main.py)"""

import pytest
import tempfile
import json
from pathlib import Path
from click.testing import CliRunner

from mossy_manager.cli.main import main


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def plugins_file(tmp_path):
    """Create a temporary plugins.txt for testing."""
    p = tmp_path / "plugins.txt"
    p.write_text(
        "# Comment\n*Fallout4.esm\n*DLCRobot.esm\n*MyMod.esp\nDisabled.esp\n"
    )
    return p


@pytest.fixture
def mods_dir(tmp_path):
    """Create a temporary mods directory with a conflict."""
    mods = tmp_path / "mods"
    (mods / "ModA" / "textures").mkdir(parents=True)
    (mods / "ModA" / "textures" / "sky.dds").write_bytes(b"tex")
    (mods / "ModB" / "textures").mkdir(parents=True)
    (mods / "ModB" / "textures" / "sky.dds").write_bytes(b"tex")
    return mods


@pytest.fixture
def patch_file(tmp_path):
    """Create a temporary patch JSON file."""
    data = {
        "name": "TestPatch",
        "description": "A test patch",
        "created_at": "2026-01-01T00:00:00",
        "operations": [
            {"type": "add", "file": "newfile.txt", "content": "hello"}
        ],
        "target_mods": [],
    }
    p = tmp_path / "TestPatch.json"
    p.write_text(json.dumps(data))
    return p


class TestCLITopLevel:
    def test_help(self, runner):
        r = runner.invoke(main, ["--help"])
        assert r.exit_code == 0
        assert "Mossy Manager" in r.output

    def test_version(self, runner):
        r = runner.invoke(main, ["--version"])
        assert r.exit_code == 0

    def test_info(self, runner):
        r = runner.invoke(main, ["info"])
        assert r.exit_code == 0
        assert "Version" in r.output

    def test_verbose_flag(self, runner, plugins_file):
        r = runner.invoke(main, ["--verbose", "loadorder", "list",
                                  "--plugins-file", str(plugins_file)])
        assert r.exit_code == 0


class TestLoadOrderCommands:
    def test_list_no_file(self, runner):
        """list with no files prints 'No plugins loaded'"""
        r = runner.invoke(main, ["loadorder", "list"])
        assert r.exit_code == 0
        assert "No plugins loaded" in r.output

    def test_list_with_plugins_file(self, runner, plugins_file):
        r = runner.invoke(main, ["loadorder", "list",
                                  "--plugins-file", str(plugins_file)])
        assert r.exit_code == 0
        assert "Fallout4.esm" in r.output

    def test_validate_valid(self, runner, plugins_file):
        r = runner.invoke(main, ["loadorder", "validate",
                                  "--plugins-file", str(plugins_file)])
        assert r.exit_code == 0

    def test_optimize(self, runner, plugins_file):
        r = runner.invoke(main, ["loadorder", "optimize",
                                  "--plugins-file", str(plugins_file)])
        assert r.exit_code == 0
        assert "Optimized" in r.output

    def test_optimize_with_output(self, runner, plugins_file, tmp_path):
        out = tmp_path / "optimized.txt"
        r = runner.invoke(main, ["loadorder", "optimize",
                                  "--plugins-file", str(plugins_file),
                                  "--output", str(out),
                                  "--apply"])
        assert r.exit_code == 0
        assert out.exists()


class TestConflictCommands:
    def test_scan_no_conflicts(self, runner, tmp_path):
        mods = tmp_path / "mods"
        (mods / "ModA").mkdir(parents=True)
        r = runner.invoke(main, ["conflicts", "scan", "--mods-dir", str(mods)])
        assert r.exit_code == 0
        assert "Scanned" in r.output

    def test_scan_with_conflicts(self, runner, mods_dir):
        r = runner.invoke(main, ["conflicts", "scan", "--mods-dir", str(mods_dir)])
        assert r.exit_code == 0
        assert "Conflict" in r.output or "conflict" in r.output

    def test_scan_with_output(self, runner, mods_dir, tmp_path):
        out = tmp_path / "report.txt"
        r = runner.invoke(main, ["conflicts", "scan",
                                  "--mods-dir", str(mods_dir),
                                  "--output", str(out)])
        assert r.exit_code == 0
        assert out.exists()

    def test_xedit_help(self, runner):
        r = runner.invoke(main, ["conflicts", "xedit-help"])
        assert r.exit_code == 0
        assert "xEdit" in r.output


class TestPatchCommands:
    def test_create(self, runner, tmp_path):
        out = tmp_path / "patches"
        r = runner.invoke(main, ["patch", "create",
                                  "--name", "MyPatch",
                                  "--description", "Test",
                                  "--output", str(out)])
        assert r.exit_code == 0
        assert "MyPatch" in r.output
        assert (out / "MyPatch.json").exists()

    def test_list_patches(self, runner, tmp_path):
        patches_dir = tmp_path / "patches"
        patches_dir.mkdir()
        # Create a patch file
        data = {"name": "ExistingPatch", "description": "", "operations": [],
                "target_mods": [], "created_at": ""}
        (patches_dir / "ExistingPatch.json").write_text(json.dumps(data))
        r = runner.invoke(main, ["patch", "list", "--patches-dir", str(patches_dir)])
        assert r.exit_code == 0
        assert "ExistingPatch" in r.output

    def test_list_patches_empty(self, runner, tmp_path):
        empty = tmp_path / "empty_patches"
        empty.mkdir()
        r = runner.invoke(main, ["patch", "list", "--patches-dir", str(empty)])
        assert r.exit_code == 0
        assert "No patches found" in r.output

    def test_apply_patch(self, runner, patch_file, tmp_path):
        mod_dir = tmp_path / "mod"
        mod_dir.mkdir()
        r = runner.invoke(main, ["patch", "apply",
                                  "--patch-file", str(patch_file),
                                  "--mod-dir", str(mod_dir)])
        assert r.exit_code == 0
        assert "applied" in r.output.lower() or "success" in r.output.lower()

    def test_apply_patch_dry_run(self, runner, patch_file, tmp_path):
        mod_dir = tmp_path / "mod"
        mod_dir.mkdir()
        r = runner.invoke(main, ["patch", "apply",
                                  "--patch-file", str(patch_file),
                                  "--mod-dir", str(mod_dir),
                                  "--dry-run"])
        assert r.exit_code == 0
        assert "DRY RUN" in r.output


class TestResolveXeditCommand:
    def test_resolve_xedit_no_conflicts(self, runner, tmp_path):
        mods = tmp_path / "mods"
        (mods / "ModA").mkdir(parents=True)
        r = runner.invoke(main, ["conflicts", "resolve-xedit",
                                  "--mods-dir", str(mods)])
        assert r.exit_code == 0
        assert "No conflicts detected" in r.output

    def test_resolve_xedit_with_conflicts(self, runner, mods_dir, tmp_path):
        out = tmp_path / "xedit_out"
        r = runner.invoke(main, ["conflicts", "resolve-xedit",
                                  "--mods-dir", str(mods_dir),
                                  "--output-dir", str(out),
                                  "--apply"])
        assert r.exit_code == 0
        assert out.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
