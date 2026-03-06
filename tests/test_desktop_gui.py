"""
Tests for the standalone desktop GUI module (mossy_manager.gui).

These tests run headlessly — no display is required.  They verify that:
  - The GUI module can be imported
  - The palette and style constants are correct
  - DesktopApp raises a clean RuntimeError when tkinter is unavailable
  - The launch() function is importable and callable (headless guard)
  - The UI_MANIFEST file exists and declares ui_type = standalone
  - The CLI 'mossy ui' command no longer starts a web server
"""

import importlib
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from mossy_manager.cli.main import main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent


def _fake_tkinter():
    """Return a minimal fake tkinter module tree."""
    tk = types.ModuleType("tkinter")
    tk.Tk = MagicMock()
    tk.Frame = MagicMock()
    tk.Label = MagicMock()
    tk.Text = MagicMock()
    tk.Listbox = MagicMock()
    # Geometry / layout constants
    tk.BOTH = "both"
    tk.BOTTOM = "bottom"
    tk.CENTER = "center"
    tk.DISABLED = "disabled"
    tk.E = "e"
    tk.END = "end"
    tk.LEFT = "left"
    tk.MULTIPLE = "multiple"
    tk.NORMAL = "normal"
    tk.RIGHT = "right"
    tk.TOP = "top"
    tk.W = "w"
    tk.X = "x"
    tk.Y = "y"
    tk.WORD = "word"
    tk.VERTICAL = "vertical"
    tk.HORIZONTAL = "horizontal"
    tk.StringVar = MagicMock(return_value=MagicMock(get=MagicMock(return_value=""),
                                                    set=MagicMock()))
    tk.BooleanVar = MagicMock(return_value=MagicMock(get=MagicMock(return_value=False)))

    ttk = types.ModuleType("tkinter.ttk")
    ttk.Style = MagicMock()
    ttk.Button = MagicMock()
    ttk.Checkbutton = MagicMock()
    ttk.Combobox = MagicMock()
    ttk.Entry = MagicMock()
    ttk.Notebook = MagicMock()
    ttk.Scrollbar = MagicMock()
    ttk.Treeview = MagicMock()
    tk.ttk = ttk

    msgbox = types.ModuleType("tkinter.messagebox")
    msgbox.showerror = MagicMock()
    msgbox.showwarning = MagicMock()
    tk.messagebox = msgbox

    filedialog = types.ModuleType("tkinter.filedialog")
    filedialog.askopenfilename = MagicMock(return_value="")
    tk.filedialog = filedialog

    font_mod = types.ModuleType("tkinter.font")
    tk.font = font_mod

    return tk, ttk, msgbox, filedialog, font_mod


# ---------------------------------------------------------------------------
# UI_MANIFEST tests
# ---------------------------------------------------------------------------

class TestUIManifest:
    def test_manifest_exists(self):
        assert (REPO_ROOT / "UI_MANIFEST").exists(), "UI_MANIFEST file is missing"

    def test_manifest_declares_standalone(self):
        """Parse UI_MANIFEST as an ini file and check ui_type = standalone."""
        import configparser
        cfg = configparser.ConfigParser()
        cfg.read(REPO_ROOT / "UI_MANIFEST")
        assert cfg.has_section("ui"), "UI_MANIFEST must have a [ui] section"
        assert cfg.get("ui", "ui_type").strip() == "standalone", (
            "UI_MANIFEST [ui] ui_type must equal 'standalone'"
        )

    def test_manifest_references_tkinter(self):
        """The [ui] toolkit value should name tkinter."""
        import configparser
        cfg = configparser.ConfigParser()
        cfg.read(REPO_ROOT / "UI_MANIFEST")
        assert "tkinter" in cfg.get("ui", "toolkit", fallback="").lower()

    def test_manifest_warns_against_web_conversion(self):
        """The manifest prose must contain an explicit DO NOT / MUST NOT warning."""
        text = (REPO_ROOT / "UI_MANIFEST").read_text()
        assert "web" in text.lower()
        assert "DO NOT" in text or "MUST NOT" in text


# ---------------------------------------------------------------------------
# GUI module import / structure tests
# ---------------------------------------------------------------------------

class TestGuiModuleStructure:
    def test_gui_package_importable(self):
        gui = importlib.import_module("mossy_manager.gui")
        assert hasattr(gui, "DesktopApp")
        assert hasattr(gui, "launch")

    def test_palette_keys_present(self):
        from mossy_manager.gui.app import PALETTE
        for key in ("bg", "bg_dark", "accent", "text", "success", "danger"):
            assert key in PALETTE, f"PALETTE missing key: {key}"

    def test_palette_values_are_hex_colours(self):
        from mossy_manager.gui.app import PALETTE
        for k, v in PALETTE.items():
            assert v.startswith("#"), f"PALETTE[{k}] = {v!r} is not a hex colour"
            assert len(v) == 7, f"PALETTE[{k}] = {v!r} has wrong length"

    def test_desktop_app_class_exists(self):
        from mossy_manager.gui.app import DesktopApp
        assert callable(DesktopApp)

    def test_launch_function_exists(self):
        from mossy_manager.gui.app import launch
        assert callable(launch)


# ---------------------------------------------------------------------------
# DesktopApp: tkinter unavailable → clean error
# ---------------------------------------------------------------------------

class TestDesktopAppNoTkinter:
    def test_raises_when_tkinter_missing(self, monkeypatch):
        """DesktopApp should raise RuntimeError if tkinter is not available."""
        import mossy_manager.gui.app as gui_mod
        monkeypatch.setattr(gui_mod, "_TKINTER_AVAILABLE", False)
        with pytest.raises(RuntimeError, match="tkinter"):
            gui_mod.DesktopApp()

    def test_launch_raises_when_tkinter_missing(self, monkeypatch):
        """launch() should raise RuntimeError if tkinter is not available."""
        import mossy_manager.gui.app as gui_mod
        monkeypatch.setattr(gui_mod, "_TKINTER_AVAILABLE", False)
        with pytest.raises(RuntimeError, match="tkinter"):
            gui_mod.launch()


# ---------------------------------------------------------------------------
# DesktopApp: construction with mocked tkinter
# ---------------------------------------------------------------------------

class TestDesktopAppConstruction:
    def test_constructs_with_mocked_tkinter(self, monkeypatch):
        """DesktopApp can be constructed when tkinter widgets are mocked."""
        import mossy_manager.gui.app as gui_mod

        tk_mock, ttk_mock, msgbox_mock, filedialog_mock, font_mock = _fake_tkinter()

        # Patch _TKINTER_AVAILABLE and every symbol the module uses from tkinter.
        # These names only exist in the module when tkinter was importable; use
        # setattr so we can create them if they are absent (headless CI).
        monkeypatch.setattr(gui_mod, "_TKINTER_AVAILABLE", True)
        for attr, val in [
            ("tk",         tk_mock),
            ("ttk",        ttk_mock),
            ("messagebox", msgbox_mock),
            ("filedialog", filedialog_mock),
            ("tkfont",     font_mock),
        ]:
            try:
                monkeypatch.setattr(gui_mod, attr, val)
            except AttributeError:
                setattr(gui_mod, attr, val)

        # Patch backend so no real MO2 is needed
        monkeypatch.setattr(gui_mod, "_import_backend", lambda: None)

        app = gui_mod.DesktopApp(mo2_path=None)
        assert app is not None

    def test_mo2_path_stored(self, monkeypatch):
        import mossy_manager.gui.app as gui_mod
        tk_mock, ttk_mock, msgbox_mock, filedialog_mock, font_mock = _fake_tkinter()
        monkeypatch.setattr(gui_mod, "_TKINTER_AVAILABLE", True)
        for attr, val in [
            ("tk",         tk_mock),
            ("ttk",        ttk_mock),
            ("messagebox", msgbox_mock),
            ("filedialog", filedialog_mock),
            ("tkfont",     font_mock),
        ]:
            try:
                monkeypatch.setattr(gui_mod, attr, val)
            except AttributeError:
                setattr(gui_mod, attr, val)
        monkeypatch.setattr(gui_mod, "_import_backend", lambda: None)

        app = gui_mod.DesktopApp(mo2_path="C:/MO2")
        assert app._mo2_path_override == "C:/MO2"


# ---------------------------------------------------------------------------
# CLI: 'mossy ui' no longer starts a web server
# ---------------------------------------------------------------------------

class TestCLIUiCommand:
    def test_ui_command_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["ui", "--help"])
        assert result.exit_code == 0
        # Must mention desktop / standalone — not web server / browser
        output = result.output.lower()
        assert "desktop" in output or "standalone" in output or "tkinter" in output

    def test_ui_command_does_not_open_browser(self):
        runner = CliRunner()
        result = runner.invoke(main, ["ui", "--help"])
        output = result.output.lower()
        # The help text must not describe opening a browser or starting a server
        assert "opening browser" not in output
        assert "open browser" not in output
        assert "starting web server" not in output
        assert "uvicorn" not in output

    def test_ui_command_accepts_mo2_path_option(self):
        runner = CliRunner()
        result = runner.invoke(main, ["ui", "--help"])
        assert "--mo2-path" in result.output or "-m" in result.output

    def test_ui_command_calls_launch(self, monkeypatch):
        """'mossy ui' must call gui.app.launch(), not uvicorn.run()."""
        called_with = {}

        def fake_launch(mo2_path=None):
            called_with["mo2_path"] = mo2_path

        import mossy_manager.gui.app as gui_mod
        monkeypatch.setattr(gui_mod, "launch", fake_launch)

        runner = CliRunner()
        result = runner.invoke(main, ["ui"])
        assert result.exit_code == 0
        assert "mo2_path" in called_with  # launch() was invoked

    def test_ui_command_passes_mo2_path(self, monkeypatch):
        """--mo2-path argument must be forwarded to launch()."""
        called_with = {}

        def fake_launch(mo2_path=None):
            called_with["mo2_path"] = mo2_path

        import mossy_manager.gui.app as gui_mod
        monkeypatch.setattr(gui_mod, "launch", fake_launch)

        runner = CliRunner()
        result = runner.invoke(main, ["ui", "--mo2-path", "C:/Games/MO2"])
        assert result.exit_code == 0
        assert called_with.get("mo2_path") == "C:/Games/MO2"

    def test_uvicorn_not_imported_by_cli(self):
        """The CLI must NOT import uvicorn in any form."""
        import ast
        cli_src = (REPO_ROOT / "src" / "mossy_manager" / "cli" / "main.py").read_text()
        tree = ast.parse(cli_src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "uvicorn", (
                        "cli/main.py must not import uvicorn"
                    )
            elif isinstance(node, ast.ImportFrom):
                assert node.module != "uvicorn", (
                    "cli/main.py must not import from uvicorn"
                )

    def test_webbrowser_not_imported_by_cli(self):
        """The CLI must NOT import webbrowser in any form."""
        import ast
        cli_src = (REPO_ROOT / "src" / "mossy_manager" / "cli" / "main.py").read_text()
        tree = ast.parse(cli_src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "webbrowser", (
                        "cli/main.py must not import webbrowser"
                    )


# ---------------------------------------------------------------------------
# CLI: 'mossy info' reflects desktop UI
# ---------------------------------------------------------------------------

class TestCLIInfoCommand:
    def test_info_mentions_desktop_ui(self):
        runner = CliRunner()
        result = runner.invoke(main, ["info"])
        assert result.exit_code == 0
        output = result.output.lower()
        assert "desktop" in output or "standalone" in output or "tkinter" in output

    def test_info_does_not_say_web_ui(self):
        runner = CliRunner()
        result = runner.invoke(main, ["info"])
        assert "Web UI" not in result.output


# ---------------------------------------------------------------------------
# MossyManager_gui.py entry-point script
# ---------------------------------------------------------------------------

class TestGuiEntryPoint:
    def test_entry_point_exists(self):
        assert (REPO_ROOT / "MossyManager_gui.py").exists()

    def test_entry_point_imports_launch(self):
        text = (REPO_ROOT / "MossyManager_gui.py").read_text()
        assert "from mossy_manager.gui.app import launch" in text

    def test_entry_point_has_main_guard(self):
        text = (REPO_ROOT / "MossyManager_gui.py").read_text()
        assert '__name__ == "__main__"' in text or "__name__ == '__main__'" in text
