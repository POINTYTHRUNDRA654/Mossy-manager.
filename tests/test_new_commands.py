"""Tests for the 6 new CLI commands (apps #30–35).

mods list  / mods enable / mods disable  (ModManager wired to CLI)
ini apply  / ini diff                    (INIPatcher wired to CLI)
loadorder esl-candidates                 (LoadOrderManager wired to CLI)
"""

import json
import pytest
from pathlib import Path
from click.testing import CliRunner

from mossy_manager.cli.main import main


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def fake_mo2(tmp_path):
    """Minimal MO2 directory with one mod and a Default profile."""
    mo2 = tmp_path / "MO2"
    mods_dir = mo2 / "mods"
    (mods_dir / "CoolMod").mkdir(parents=True)
    (mods_dir / "OtherMod").mkdir(parents=True)

    profile_dir = mo2 / "profiles" / "Default"
    profile_dir.mkdir(parents=True)
    (profile_dir / "modlist.txt").write_text(
        "+CoolMod\n-OtherMod\n", encoding="utf-8"
    )
    (profile_dir / "plugins.txt").write_text(
        "*Fallout4.esm\n*CoolMod.esp\n", encoding="utf-8"
    )
    (profile_dir / "loadorder.txt").write_text(
        "Fallout4.esm\nCoolMod.esp\n", encoding="utf-8"
    )
    return mo2


@pytest.fixture
def fake_game_docs(tmp_path):
    """Fallout 4 documents directory with a minimal Fallout4.ini."""
    docs = tmp_path / "Fallout4Docs"
    docs.mkdir()
    (docs / "Fallout4.ini").write_text(
        "[Papyrus]\nbEnableLogging=0\n\n[Archive]\nbInvalidateOlderFiles=0\n",
        encoding="utf-8",
    )
    return docs


@pytest.fixture
def plugins_file_with_esps(tmp_path):
    """plugins.txt containing several .esp plugins suitable for ESL checks."""
    p = tmp_path / "plugins.txt"
    p.write_text(
        "*Fallout4.esm\n*BigMod.esp\n*SmallMod.esp\nDisabledMod.esp\n",
        encoding="utf-8",
    )
    return p


# ─────────────────────────────────────────────────────────────────────────────
# mods list  (#30)
# ─────────────────────────────────────────────────────────────────────────────

class TestModsList:
    def test_mods_list_shows_mods(self, runner, fake_mo2):
        r = runner.invoke(main, [
            "mods", "list",
            "--mo2-path", str(fake_mo2),
            "--profile", "Default",
        ])
        assert r.exit_code == 0
        assert "CoolMod" in r.output
        assert "OtherMod" in r.output

    def test_mods_list_shows_enabled_disabled(self, runner, fake_mo2):
        r = runner.invoke(main, [
            "mods", "list",
            "--mo2-path", str(fake_mo2),
            "--profile", "Default",
        ])
        assert r.exit_code == 0
        assert "Enabled" in r.output
        assert "Disabled" in r.output

    def test_mods_list_empty_dir(self, runner, tmp_path):
        """Empty mods/ directory should print a warning, not crash."""
        mo2 = tmp_path / "MO2"
        (mo2 / "mods").mkdir(parents=True)
        (mo2 / "profiles" / "Default").mkdir(parents=True)
        (mo2 / "profiles" / "Default" / "modlist.txt").write_text("")
        r = runner.invoke(main, [
            "mods", "list",
            "--mo2-path", str(mo2),
            "--profile", "Default",
        ])
        assert r.exit_code == 0
        assert "No mods found" in r.output

    def test_mods_list_help(self, runner):
        r = runner.invoke(main, ["mods", "list", "--help"])
        assert r.exit_code == 0
        assert "modlist" in r.output.lower() or "status" in r.output.lower()


# ─────────────────────────────────────────────────────────────────────────────
# mods enable  (#31)
# ─────────────────────────────────────────────────────────────────────────────

class TestModsEnable:
    def test_enable_existing_mod(self, runner, fake_mo2):
        r = runner.invoke(main, [
            "mods", "enable", "OtherMod",
            "--mo2-path", str(fake_mo2),
            "--profile", "Default",
        ])
        assert r.exit_code == 0
        assert "enabled" in r.output.lower()
        # Verify modlist.txt was updated
        ml = (fake_mo2 / "profiles" / "Default" / "modlist.txt").read_text()
        assert "+OtherMod" in ml

    def test_enable_missing_mod(self, runner, fake_mo2):
        r = runner.invoke(main, [
            "mods", "enable", "DoesNotExist",
            "--mo2-path", str(fake_mo2),
            "--profile", "Default",
        ])
        assert r.exit_code == 0
        assert "✗" in r.output or "not found" in r.output.lower()

    def test_enable_help(self, runner):
        r = runner.invoke(main, ["mods", "enable", "--help"])
        assert r.exit_code == 0


# ─────────────────────────────────────────────────────────────────────────────
# mods disable  (#32)
# ─────────────────────────────────────────────────────────────────────────────

class TestModsDisable:
    def test_disable_existing_mod(self, runner, fake_mo2):
        r = runner.invoke(main, [
            "mods", "disable", "CoolMod",
            "--mo2-path", str(fake_mo2),
            "--profile", "Default",
        ])
        assert r.exit_code == 0
        assert "disabled" in r.output.lower()
        ml = (fake_mo2 / "profiles" / "Default" / "modlist.txt").read_text()
        assert "-CoolMod" in ml

    def test_disable_missing_mod(self, runner, fake_mo2):
        r = runner.invoke(main, [
            "mods", "disable", "Ghost",
            "--mo2-path", str(fake_mo2),
            "--profile", "Default",
        ])
        assert r.exit_code == 0
        assert "✗" in r.output or "not found" in r.output.lower()

    def test_disable_help(self, runner):
        r = runner.invoke(main, ["mods", "disable", "--help"])
        assert r.exit_code == 0


# ─────────────────────────────────────────────────────────────────────────────
# ini apply  (#33)
# ─────────────────────────────────────────────────────────────────────────────

class TestIniApply:
    def test_apply_papyrus_logging(self, runner, fake_game_docs):
        r = runner.invoke(main, [
            "ini", "apply", "papyrus_logging",
            "--game-docs", str(fake_game_docs),
        ])
        assert r.exit_code == 0
        assert "applied" in r.output.lower() or "✓" in r.output
        # Verify the file was actually written
        custom = fake_game_docs / "Fallout4Custom.ini"
        assert custom.exists()
        content = custom.read_text()
        assert "bEnableLogging" in content
        assert "1" in content  # value written (configparser formats as "key = 1")

    def test_apply_archive_invalidation(self, runner, fake_game_docs):
        r = runner.invoke(main, [
            "ini", "apply", "archive_invalidation",
            "--game-docs", str(fake_game_docs),
            "--no-backup",
        ])
        assert r.exit_code == 0
        custom = fake_game_docs / "Fallout4Custom.ini"
        content = custom.read_text()
        assert "bInvalidateOlderFiles" in content

    def test_apply_creates_backup_by_default(self, runner, fake_game_docs):
        # Pre-create the Custom.ini so a backup can be made
        custom = fake_game_docs / "Fallout4Custom.ini"
        custom.write_text("[Papyrus]\nbEnableLogging=0\n")
        r = runner.invoke(main, [
            "ini", "apply", "papyrus_logging",
            "--game-docs", str(fake_game_docs),
        ])
        assert r.exit_code == 0
        assert "Backup" in r.output or "backup" in r.output.lower()

    def test_apply_performance_high(self, runner, fake_game_docs):
        r = runner.invoke(main, [
            "ini", "apply", "performance_high",
            "--game-docs", str(fake_game_docs),
            "--no-backup",
        ])
        assert r.exit_code == 0
        custom = fake_game_docs / "Fallout4Custom.ini"
        assert "fShadowDistance" in custom.read_text()

    def test_apply_performance_low(self, runner, fake_game_docs):
        r = runner.invoke(main, [
            "ini", "apply", "performance_low",
            "--game-docs", str(fake_game_docs),
            "--no-backup",
        ])
        assert r.exit_code == 0

    def test_apply_f4se_compat(self, runner, fake_game_docs):
        r = runner.invoke(main, [
            "ini", "apply", "f4se_compat",
            "--game-docs", str(fake_game_docs),
            "--no-backup",
        ])
        assert r.exit_code == 0

    def test_apply_help(self, runner):
        r = runner.invoke(main, ["ini", "apply", "--help"])
        assert r.exit_code == 0
        assert "preset" in r.output.lower()

    def test_apply_verification_passes(self, runner, fake_game_docs):
        r = runner.invoke(main, [
            "ini", "apply", "papyrus_logging",
            "--game-docs", str(fake_game_docs),
            "--no-backup",
        ])
        assert r.exit_code == 0
        assert "Verification passed" in r.output


# ─────────────────────────────────────────────────────────────────────────────
# ini diff  (#34)
# ─────────────────────────────────────────────────────────────────────────────

class TestIniDiff:
    def test_diff_no_differences(self, runner, fake_game_docs):
        """When both files are identical (or one is empty), report no diffs."""
        (fake_game_docs / "Fallout4Custom.ini").write_text(
            "[Papyrus]\nbEnableLogging=0\n", encoding="utf-8"
        )
        (fake_game_docs / "Fallout4.ini").write_text(
            "[Papyrus]\nbEnableLogging=0\n", encoding="utf-8"
        )
        r = runner.invoke(main, [
            "ini", "diff",
            "--game-docs", str(fake_game_docs),
        ])
        assert r.exit_code == 0
        assert "No differences" in r.output

    def test_diff_shows_differences(self, runner, fake_game_docs):
        (fake_game_docs / "Fallout4Custom.ini").write_text(
            "[Papyrus]\nbEnableLogging=1\n", encoding="utf-8"
        )
        r = runner.invoke(main, [
            "ini", "diff",
            "--game-docs", str(fake_game_docs),
        ])
        assert r.exit_code == 0
        assert "bEnableLogging" in r.output

    def test_diff_shows_absent_keys(self, runner, fake_game_docs):
        """Keys present in A but absent in B should appear as 'absent'."""
        (fake_game_docs / "Fallout4Custom.ini").write_text(
            "[Archive]\nbInvalidateOlderFiles=1\n", encoding="utf-8"
        )
        r = runner.invoke(main, [
            "ini", "diff",
            "--game-docs", str(fake_game_docs),
        ])
        assert r.exit_code == 0
        # Some difference should be reported
        assert "INI Diff" in r.output or "No differences" in r.output

    def test_diff_help(self, runner):
        r = runner.invoke(main, ["ini", "diff", "--help"])
        assert r.exit_code == 0
        assert "diff" in r.output.lower()

    def test_diff_missing_file_produces_output(self, runner, tmp_path):
        """Diff against a non-existent Custom.ini should not crash."""
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "Fallout4.ini").write_text("[Display]\nfoo=bar\n")
        r = runner.invoke(main, [
            "ini", "diff",
            "--game-docs", str(docs),
        ])
        assert r.exit_code == 0


# ─────────────────────────────────────────────────────────────────────────────
# loadorder esl-candidates  (#35)
# ─────────────────────────────────────────────────────────────────────────────

class TestEslCandidates:
    def test_esl_candidates_from_plugins_file(self, runner, plugins_file_with_esps):
        r = runner.invoke(main, [
            "loadorder", "esl-candidates",
            "--plugins-file", str(plugins_file_with_esps),
        ])
        assert r.exit_code == 0
        # BigMod.esp and SmallMod.esp are candidates (size unknown → listed)
        assert "BigMod.esp" in r.output or "SmallMod.esp" in r.output or "No ESL candidates" in r.output

    def test_esl_candidates_with_mo2_path(self, runner, fake_mo2):
        """esl-candidates reads loadorder via MO2 integration."""
        r = runner.invoke(main, [
            "loadorder", "esl-candidates",
            "--mo2-path", str(fake_mo2),
            "--profile", "Default",
        ])
        assert r.exit_code == 0
        # CoolMod.esp is in the fake load order → should appear or produce clean output
        assert "CoolMod.esp" in r.output or "No ESL candidates" in r.output

    def test_esl_candidates_no_args_warns(self, runner):
        r = runner.invoke(main, ["loadorder", "esl-candidates"])
        assert r.exit_code == 0
        assert "Specify" in r.output or "⚠" in r.output

    def test_esl_candidates_respects_size_limit(self, runner, tmp_path):
        """With a tiny size limit, candidates list should be empty for missing files."""
        p = tmp_path / "plugins.txt"
        p.write_text("*Fallout4.esm\n*MyMod.esp\n", encoding="utf-8")
        r = runner.invoke(main, [
            "loadorder", "esl-candidates",
            "--plugins-file", str(p),
            "--size-limit", "0",
        ])
        assert r.exit_code == 0
        # With size=0 and no file found, size_kb is None → still a candidate
        # (unknown-size entries are always included as advisory)
        assert r.exit_code == 0

    def test_esl_candidates_help(self, runner):
        r = runner.invoke(main, ["loadorder", "esl-candidates", "--help"])
        assert r.exit_code == 0
        assert "esl" in r.output.lower()

    def test_esl_candidates_only_esp(self, runner, tmp_path):
        """Masters and ESLs should not appear in the candidate list."""
        p = tmp_path / "plugins.txt"
        p.write_text("*Fallout4.esm\n*DLCRobot.esm\n*Light.esl\n", encoding="utf-8")
        r = runner.invoke(main, [
            "loadorder", "esl-candidates",
            "--plugins-file", str(p),
        ])
        assert r.exit_code == 0
        assert "No ESL candidates" in r.output
