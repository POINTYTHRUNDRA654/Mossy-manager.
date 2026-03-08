"""CLI tests for conflicts resolve-xedit."""

from pathlib import Path
from click.testing import CliRunner

from mossy_manager.cli.main import main as cli_main


def build_conflict_mods(root: Path) -> Path:
    """Create two mods with a shared texture to ensure a conflict."""
    mods = root / "mods"
    for mod_name in ("ModA", "ModB"):
        tex_dir = mods / mod_name / "textures"
        tex_dir.mkdir(parents=True, exist_ok=True)
        (tex_dir / "sky.dds").write_text("data")
    return mods


def test_resolve_xedit_dry_run_no_exports() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        mods_dir = build_conflict_mods(Path("."))

        result = runner.invoke(
            cli_main,
            ["conflicts", "resolve-xedit", "--mods-dir", str(mods_dir)],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert not Path("xedit_output").exists()


def test_resolve_xedit_apply_writes_exports() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        mods_dir = build_conflict_mods(Path("."))
        output_dir = Path("xedit_out")

        result = runner.invoke(
            cli_main,
            [
                "conflicts",
                "resolve-xedit",
                "--mods-dir",
                str(mods_dir),
                "--patch-name",
                "TestPatch",
                "--output-dir",
                str(output_dir),
                "--apply",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "Writing exports to" in result.output
        assert (output_dir / "TestPatch_conflicts.json").exists()
        assert (output_dir / "TestPatch_script.pas").exists()


def test_resolve_xedit_apply_creates_backup() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        mods_dir = build_conflict_mods(Path("."))
        output_dir = Path("xedit_output")
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "preexisting.txt").write_text("keep")

        result = runner.invoke(
            cli_main,
            [
                "conflicts",
                "resolve-xedit",
                "--mods-dir",
                str(mods_dir),
                "--patch-name",
                "BackupPatch",
                "--output-dir",
                str(output_dir),
                "--apply",
            ],
            catch_exceptions=False,
        )

        backups = [
            p
            for p in output_dir.parent.iterdir()
            if p.is_dir() and p.name.startswith(f"{output_dir.name}_backup_")
        ]

        assert result.exit_code == 0
        assert backups, "Expected a backup directory to be created"
        assert (output_dir / "BackupPatch_conflicts.json").exists()
        assert (output_dir / "BackupPatch_script.pas").exists()
