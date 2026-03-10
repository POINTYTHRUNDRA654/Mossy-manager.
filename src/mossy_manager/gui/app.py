"""
Mossy Manager – self-contained desktop GUI.

Provides an MO2-inspired tkinter window that manages load order, detects
conflicts, and surfaces AI recommendations — all without a web server or
browser.

See UI_MANIFEST (repository root) for the authoritative UI architecture spec.
DO NOT convert this module to a web-based UI.
"""

from __future__ import annotations

import json
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Guard: fail gracefully when running headless (e.g. CI without a display)
# ---------------------------------------------------------------------------
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog, font as tkfont
    _TKINTER_AVAILABLE = True
except ImportError:  # pragma: no cover
    _TKINTER_AVAILABLE = False

# ---------------------------------------------------------------------------
# Lazy backend imports (same logic the FastAPI app uses but called directly)
# ---------------------------------------------------------------------------

def _import_backend():
    """Return a dict of backend callables, or None if unavailable."""
    try:
        from mossy_manager.integrations.mo2 import MO2Integration
        from mossy_manager.games.fallout4 import Fallout4Rules
        from mossy_manager.core.conflict_resolver import ConflictResolver
        from mossy_manager.config_manager import ConfigManager
        from mossy_manager.utils.xedit_integration import XEditIntegration
        import mossy_manager
        return {
            "MO2Integration": MO2Integration,
            "Fallout4Rules": Fallout4Rules,
            "ConflictResolver": ConflictResolver,
            "ConfigManager": ConfigManager,
            "XEditIntegration": XEditIntegration,
            "version": getattr(mossy_manager, "__version__", "1.0.0"),
        }
    except Exception:  # pragma: no cover
        return None


# ---------------------------------------------------------------------------
# MO2-inspired colour palette (mirrors the CSS variables in index.html)
# ---------------------------------------------------------------------------
PALETTE = {
    "bg":           "#2b2b2b",
    "bg_dark":      "#1e1e1e",
    "bg_panel":     "#323232",
    "bg_header":    "#252525",
    "bg_toolbar":   "#3a3a3a",
    "bg_row_alt":   "#2e2e2e",
    "bg_row_hover": "#3d4f3d",
    "bg_row_sel":   "#3a5c3a",
    "bg_input":     "#1e1e1e",
    "text":         "#dcdcdc",
    "text_dim":     "#aaaaaa",
    "text_head":    "#ffffff",
    "border":       "#484848",
    "accent":       "#5c8e5c",
    "accent_hover": "#6aad6a",
    "btn_bg":       "#4a5a4a",
    "btn_hover":    "#5a6e5a",
    "danger":       "#b85c5c",
    "warn":         "#b8963c",
    "success":      "#5c9e5c",
    "esm":          "#7ab4d4",
    "esl":          "#c8a060",
    "esp":          "#9090b4",
}

_FONT_UI    = ("Segoe UI", 9)
_FONT_MONO  = ("Consolas", 9)
_FONT_HEAD  = ("Segoe UI", 9, "bold")
_FONT_SMALL = ("Segoe UI", 8)


# ---------------------------------------------------------------------------
# Helper: apply dark theme to all ttk widgets
# ---------------------------------------------------------------------------

def _apply_dark_style(style: ttk.Style) -> None:
    """Configure ttk.Style to use the MO2-inspired dark palette."""
    p = PALETTE

    style.theme_use("clam")

    # Frame / Label / Entry
    style.configure("TFrame",         background=p["bg"])
    style.configure("Panel.TFrame",   background=p["bg_panel"])
    style.configure("Header.TFrame",  background=p["bg_header"])
    style.configure("Toolbar.TFrame", background=p["bg_toolbar"])
    style.configure("TLabel",         background=p["bg"],       foreground=p["text"],     font=_FONT_UI)
    style.configure("Dim.TLabel",     background=p["bg"],       foreground=p["text_dim"], font=_FONT_SMALL)
    style.configure("Head.TLabel",    background=p["bg_header"],foreground=p["text_head"],font=_FONT_HEAD)
    style.configure("Panel.TLabel",   background=p["bg_panel"], foreground=p["text"],     font=_FONT_UI)
    style.configure("Toolbar.TLabel", background=p["bg_toolbar"],foreground=p["text_dim"],font=_FONT_SMALL)

    # Entry (text input)
    style.configure("TEntry",
                    fieldbackground=p["bg_input"],
                    foreground=p["text"],
                    insertcolor=p["text"],
                    bordercolor=p["border"],
                    font=_FONT_UI)

    # Combobox (profile selector)
    style.configure("TCombobox",
                    fieldbackground=p["bg_input"],
                    background=p["bg_toolbar"],
                    foreground=p["text"],
                    selectbackground=p["bg_row_sel"],
                    selectforeground=p["text_head"],
                    arrowcolor=p["text_dim"],
                    font=_FONT_UI)
    style.map("TCombobox",
              fieldbackground=[("readonly", p["bg_input"])],
              foreground=[("readonly", p["text"])])

    # Button
    style.configure("TButton",
                    background=p["btn_bg"],
                    foreground=p["text"],
                    bordercolor=p["border"],
                    focuscolor=p["border"],
                    font=_FONT_UI,
                    padding=(6, 3))
    style.map("TButton",
              background=[("active", p["btn_hover"]), ("pressed", p["btn_bg"])],
              foreground=[("disabled", p["text_dim"])])

    # Primary (green-accent) button
    style.configure("Primary.TButton",
                    background=p["accent"],
                    foreground=p["text_head"],
                    bordercolor="#3d6e3d",
                    font=("Segoe UI", 9, "bold"),
                    padding=(6, 3))
    style.map("Primary.TButton",
              background=[("active", p["accent_hover"]), ("pressed", p["accent"])],
              foreground=[("disabled", p["text_dim"])])

    # Checkbutton
    style.configure("TCheckbutton",
                    background=p["bg_toolbar"],
                    foreground=p["text_dim"],
                    indicatorcolor=p["bg_input"],
                    focuscolor=p["border"],
                    font=_FONT_SMALL)
    style.map("TCheckbutton",
              background=[("active", p["bg_toolbar"])],
              indicatorcolor=[("selected", p["accent"])])

    # Notebook (tabs)
    style.configure("TNotebook",
                    background=p["bg_header"],
                    bordercolor=p["border"],
                    tabmargins=[0, 0, 0, 0])
    style.configure("TNotebook.Tab",
                    background=p["bg_toolbar"],
                    foreground=p["text_dim"],
                    font=_FONT_UI,
                    padding=(10, 4))
    style.map("TNotebook.Tab",
              background=[("selected", p["bg"]), ("active", p["bg_toolbar"])],
              foreground=[("selected", p["text_head"]), ("active", p["text"])],
              bordercolor=[("selected", p["accent"])])

    # Treeview (plugin list)
    style.configure("Treeview",
                    background=p["bg_panel"],
                    foreground=p["text"],
                    fieldbackground=p["bg_panel"],
                    bordercolor=p["border"],
                    rowheight=22,
                    font=_FONT_UI)
    style.configure("Treeview.Heading",
                    background=p["bg_header"],
                    foreground=p["text_dim"],
                    bordercolor=p["border"],
                    font=_FONT_HEAD,
                    relief="flat")
    style.map("Treeview",
              background=[("selected", p["bg_row_sel"])],
              foreground=[("selected", p["text_head"])])

    # Scrollbar
    style.configure("TScrollbar",
                    background=p["bg_panel"],
                    troughcolor=p["bg_dark"],
                    bordercolor=p["border"],
                    arrowcolor=p["text_dim"])


# ---------------------------------------------------------------------------
# Main application window
# ---------------------------------------------------------------------------

class DesktopApp:
    """
    Self-contained MO2-style desktop window for Mossy Manager.

    All backend operations are performed via direct Python calls — no HTTP
    server is started and no browser is opened.
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, mo2_path: Optional[str] = None) -> None:
        if not _TKINTER_AVAILABLE:
            raise RuntimeError(
                "tkinter is not available in this Python installation. "
                "Install a Python distribution that includes tkinter (e.g. python3-tk)."
            )

        self._mo2_path_override = mo2_path
        self._backend = _import_backend()
        self._mo2: Any = None  # MO2Integration instance, set after detection
        self._profiles: List[str] = []
        self._load_order: List[str] = []
        self._enabled: Dict[str, bool] = {}
        self._last_optimized: Optional[List[str]] = None  # Store last optimization result

        # Tk root
        self._root = tk.Tk()
        self._root.title("Mossy Manager")
        self._root.geometry("1100x680")
        self._root.minsize(800, 500)
        self._root.configure(background=PALETTE["bg_dark"])

        # ttk style
        self._style = ttk.Style(self._root)
        _apply_dark_style(self._style)

        # String vars
        self._sv_status   = tk.StringVar(value="Ready")
        self._sv_profile  = tk.StringVar()
        self._sv_mo2_path = tk.StringVar(value="Detecting MO2…")
        self._sv_xedit    = tk.StringVar(value="xEdit: ?")
        self._sv_version  = tk.StringVar(value="v1.0.0")

        # Option vars
        self._var_apply   = tk.BooleanVar(value=False)
        self._var_backup  = tk.BooleanVar(value=True)
        self._var_scan    = tk.BooleanVar(value=False)
        self._var_resolve = tk.BooleanVar(value=False)
        self._sv_patch    = tk.StringVar(value="MossyManager_ConflictPatch")
        self._sv_xedit_p  = tk.StringVar(value="")

        self._busy = False

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction helpers
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = self._root

        # Title bar
        self._build_title_bar(root)

        # Toolbar
        self._build_toolbar(root)

        # Main content area (left + right panes)
        content = tk.Frame(root, background=PALETTE["bg_dark"])
        content.pack(fill=tk.BOTH, expand=True)
        self._build_left_pane(content)
        self._build_right_pane(content)

        # Status bar
        self._build_status_bar(root)

    def _build_title_bar(self, parent: tk.Widget) -> None:
        bar = tk.Frame(parent, background=PALETTE["bg_header"], height=30)
        bar.pack(fill=tk.X, side=tk.TOP)
        bar.pack_propagate(False)

        tk.Label(bar, text="Mossy Manager",
                 bg=PALETTE["bg_header"], fg=PALETTE["text_head"],
                 font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, padx=(10, 4), pady=4)
        tk.Label(bar, textvariable=self._sv_version,
                 bg=PALETTE["bg_header"], fg=PALETTE["text_dim"],
                 font=_FONT_SMALL).pack(side=tk.LEFT, pady=4)

        tk.Label(bar, textvariable=self._sv_xedit,
                 bg=PALETTE["bg_dark"], fg=PALETTE["text_dim"],
                 font=_FONT_SMALL, relief="flat",
                 padx=6, pady=2).pack(side=tk.RIGHT, padx=4, pady=4)

        # MO2 path with browse button
        mo2_frame = tk.Frame(bar, bg=PALETTE["bg_dark"])
        mo2_frame.pack(side=tk.RIGHT, padx=4, pady=4)

        self._btn_browse_mo2 = ttk.Button(mo2_frame, text="...", width=3,
                                           command=self._browse_mo2_path)
        self._btn_browse_mo2.pack(side=tk.RIGHT, padx=(4, 0))

        tk.Label(mo2_frame, textvariable=self._sv_mo2_path,
                 bg=PALETTE["bg_dark"], fg=PALETTE["text_dim"],
                 font=_FONT_SMALL, relief="flat",
                 padx=6, pady=2).pack(side=tk.RIGHT)

    def _build_toolbar(self, parent: tk.Widget) -> None:
        bar = tk.Frame(parent, background=PALETTE["bg_toolbar"], height=36)
        bar.pack(fill=tk.X, side=tk.TOP)
        bar.pack_propagate(False)

        # Profile selector
        tk.Label(bar, text="Profile:", bg=PALETTE["bg_toolbar"], fg=PALETTE["text_dim"],
                 font=_FONT_SMALL).pack(side=tk.LEFT, padx=(8, 2), pady=6)
        self._profile_cb = ttk.Combobox(bar, textvariable=self._sv_profile,
                                        state="readonly", width=18, font=_FONT_UI)
        self._profile_cb.pack(side=tk.LEFT, pady=6, padx=(0, 4))
        self._profile_cb.bind("<<ComboboxSelected>>", lambda _: self._on_profile_change())

        self._btn_refresh = ttk.Button(bar, text="↺ Refresh",
                                       command=self._refresh_load_order)
        self._btn_refresh.pack(side=tk.LEFT, padx=2, pady=5)

        # Separator
        tk.Frame(bar, width=1, background=PALETTE["border"]).pack(
            side=tk.LEFT, fill=tk.Y, padx=6, pady=4)

        # Action buttons
        self._btn_optimize = ttk.Button(bar, text="⚡ Optimize",
                                        style="Primary.TButton",
                                        command=self._run_optimize)
        self._btn_optimize.pack(side=tk.LEFT, padx=2, pady=5)

        self._btn_conflicts = ttk.Button(bar, text="⊙ Scan Conflicts",
                                         command=self._run_scan_conflicts)
        self._btn_conflicts.pack(side=tk.LEFT, padx=2, pady=5)

        self._btn_merge = ttk.Button(bar, text="⊕ Merge Mods",
                                     command=self._open_merge_dialog)
        self._btn_merge.pack(side=tk.LEFT, padx=2, pady=5)

        # Separator
        tk.Frame(bar, width=1, background=PALETTE["border"]).pack(
            side=tk.LEFT, fill=tk.Y, padx=6, pady=4)

        # Option checkboxes
        for text, var in [("Apply", self._var_apply),
                           ("Backup", self._var_backup),
                           ("Scan Conflicts", self._var_scan),
                           ("xEdit Resolve", self._var_resolve)]:
            ttk.Checkbutton(bar, text=text, variable=var).pack(
                side=tk.LEFT, padx=4, pady=5)

    def _build_left_pane(self, parent: tk.Widget) -> None:
        frame = tk.Frame(parent, background=PALETTE["bg_panel"],
                         relief="flat", bd=0)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False,
                   padx=(0, 0), pady=0)
        frame.configure(width=380)
        frame.pack_propagate(False)

        # Pane header
        hdr = tk.Frame(frame, background=PALETTE["bg_header"], height=26)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Plugins", bg=PALETTE["bg_header"], fg=PALETTE["text_head"],
                 font=_FONT_HEAD).pack(side=tk.LEFT, padx=8, pady=4)
        self._lbl_count = tk.Label(hdr, text="0",
                                   bg=PALETTE["bg_dark"], fg=PALETTE["text_dim"],
                                   font=_FONT_SMALL, padx=5, pady=1)
        self._lbl_count.pack(side=tk.LEFT, pady=4)

        # Plugin list treeview
        cols = ("#", "Active", "Name", "Type")
        self._tree = ttk.Treeview(frame, columns=cols, show="headings",
                                  selectmode="browse")
        self._tree.heading("#",      text="#",      anchor=tk.E)
        self._tree.heading("Active", text="Active", anchor=tk.CENTER)
        self._tree.heading("Name",   text="Name",   anchor=tk.W)
        self._tree.heading("Type",   text="Type",   anchor=tk.W)
        self._tree.column("#",      width=36,  stretch=False, anchor=tk.E)
        self._tree.column("Active", width=48,  stretch=False, anchor=tk.CENTER)
        self._tree.column("Name",   width=230, stretch=True,  anchor=tk.W)
        self._tree.column("Type",   width=52,  stretch=False, anchor=tk.W)

        # Alternating row colours
        self._tree.tag_configure("even",    background=PALETTE["bg_row_alt"])
        self._tree.tag_configure("odd",     background=PALETTE["bg_panel"])
        self._tree.tag_configure("esm_tag", foreground=PALETTE["esm"])
        self._tree.tag_configure("esl_tag", foreground=PALETTE["esl"])
        self._tree.tag_configure("esp_tag", foreground=PALETTE["esp"])

        vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)

        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree.pack(fill=tk.BOTH, expand=True)

    def _build_right_pane(self, parent: tk.Widget) -> None:
        frame = tk.Frame(parent, background=PALETTE["bg"])
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._notebook = ttk.Notebook(frame)
        self._notebook.pack(fill=tk.BOTH, expand=True)

        self._tab_results   = self._build_tab_results()
        self._tab_conflicts = self._build_tab_conflicts()
        self._tab_ai        = self._build_tab_ai()
        self._tab_settings  = self._build_tab_settings()

        self._notebook.add(self._tab_results,   text="Results")
        self._notebook.add(self._tab_conflicts, text="Conflicts")
        self._notebook.add(self._tab_ai,        text="AI Advice")
        self._notebook.add(self._tab_settings,  text="Settings")

    def _make_tab_frame(self) -> tk.Frame:
        f = tk.Frame(self._notebook, background=PALETTE["bg"])
        return f

    def _section(self, parent: tk.Widget, title: str) -> Tuple[tk.Frame, tk.Frame]:
        """Return (outer_frame, body_frame) for a labelled section block."""
        outer = tk.Frame(parent, background=PALETTE["bg_panel"],
                         relief="flat", bd=1,
                         highlightbackground=PALETTE["border"],
                         highlightthickness=1)
        outer.pack(fill=tk.X, pady=(0, 6))

        hdr = tk.Frame(outer, background=PALETTE["bg_header"], height=22)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text=title, bg=PALETTE["bg_header"], fg=PALETTE["text_head"],
                 font=_FONT_HEAD).pack(side=tk.LEFT, padx=8, pady=3)

        body = tk.Frame(outer, background=PALETTE["bg_panel"])
        body.pack(fill=tk.X, padx=8, pady=6)
        return outer, body

    def _stat_grid(self, parent: tk.Widget,
                   labels: List[str]) -> Dict[str, tk.StringVar]:
        """Build a row of stat boxes; returns a dict of StringVar per label."""
        grid = tk.Frame(parent, background=PALETTE["bg"])
        grid.pack(fill=tk.X, pady=(0, 6))
        vars_: Dict[str, tk.StringVar] = {}
        for i, lbl in enumerate(labels):
            sv = tk.StringVar(value="–")
            vars_[lbl] = sv
            box = tk.Frame(grid, background=PALETTE["bg_dark"],
                           relief="flat", bd=1,
                           highlightbackground=PALETTE["border"],
                           highlightthickness=1)
            box.grid(row=0, column=i, padx=3, pady=3, sticky="nsew")
            tk.Label(box, text=lbl, bg=PALETTE["bg_dark"], fg=PALETTE["text_dim"],
                     font=_FONT_SMALL).pack(anchor=tk.W, padx=6, pady=(4, 0))
            tk.Label(box, textvariable=sv,
                     bg=PALETTE["bg_dark"], fg=PALETTE["text_head"],
                     font=("Segoe UI", 14, "bold")).pack(anchor=tk.W, padx=6, pady=(0, 4))
            grid.columnconfigure(i, weight=1)
        return vars_

    def _scrolled_text(self, parent: tk.Widget, height: int = 8) -> tk.Text:
        """Return a read-only dark-themed Text widget with a scrollbar."""
        frm = tk.Frame(parent, background=PALETTE["bg_dark"])
        frm.pack(fill=tk.BOTH, expand=True)
        txt = tk.Text(frm, height=height,
                      bg=PALETTE["bg_dark"], fg=PALETTE["text"],
                      insertbackground=PALETTE["text"],
                      font=_FONT_MONO,
                      relief="flat", wrap=tk.WORD,
                      selectbackground=PALETTE["bg_row_sel"],
                      selectforeground=PALETTE["text_head"])
        vsb = ttk.Scrollbar(frm, orient=tk.VERTICAL, command=txt.yview)
        txt.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        txt.pack(fill=tk.BOTH, expand=True)
        txt.configure(state=tk.DISABLED)
        return txt

    # ---- Results tab ----

    def _build_tab_results(self) -> tk.Frame:
        tab = self._make_tab_frame()
        inner = tk.Frame(tab, background=PALETTE["bg"])
        inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        sv = self._stat_grid(inner, ["Status", "Errors", "Warnings", "Recommendations"])
        self._sv_stat_status = sv["Status"]
        self._sv_stat_err    = sv["Errors"]
        self._sv_stat_warn   = sv["Warnings"]
        self._sv_stat_rec    = sv["Recommendations"]
        self._sv_stat_status.set("Ready")

        _, body_order = self._section(inner, "Optimized Load Order Preview")
        self._txt_results = self._scrolled_text(body_order, height=10)

        # Add "Apply Load Order" button (hidden initially)
        btn_frame = tk.Frame(body_order, background=PALETTE["bg_panel"])
        btn_frame.pack(fill=tk.X, pady=(6, 0))

        self._btn_apply_load_order = ttk.Button(
            btn_frame,
            text="Apply This Load Order",
            command=self._apply_last_optimization,
            style="Accent.TButton"
        )
        self._btn_apply_load_order.pack(side=tk.LEFT, padx=4)

        # Initially hide the button
        btn_frame.pack_forget()
        self._apply_button_frame = btn_frame

        _, body_rec = self._section(inner, "Recommendations")
        self._txt_recs = self._scrolled_text(body_rec, height=5)

        return tab

    # ---- Conflicts tab ----

    def _build_tab_conflicts(self) -> tk.Frame:
        tab = self._make_tab_frame()
        inner = tk.Frame(tab, background=PALETTE["bg"])
        inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        sv = self._stat_grid(inner, ["Mods Scanned", "Critical", "High", "Medium", "Low"])
        self._sv_cs_mods     = sv["Mods Scanned"]
        self._sv_cs_critical = sv["Critical"]
        self._sv_cs_high     = sv["High"]
        self._sv_cs_medium   = sv["Medium"]
        self._sv_cs_low      = sv["Low"]

        _, body = self._section(inner, "Conflict Report")
        self._txt_conflicts = self._scrolled_text(body, height=14)

        return tab

    # ---- AI tab ----

    def _build_tab_ai(self) -> tk.Frame:
        tab = self._make_tab_frame()
        inner = tk.Frame(tab, background=PALETTE["bg"])
        inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        _, body = self._section(inner, "AI Advice & Analysis")
        self._txt_ai = self._scrolled_text(body, height=20)

        return tab

    # ---- Settings tab ----

    def _build_tab_settings(self) -> tk.Frame:
        tab = self._make_tab_frame()
        inner = tk.Frame(tab, background=PALETTE["bg"])
        inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        _, body_opts = self._section(inner, "Session Options")
        for text, var in [
            ("Apply changes immediately",          self._var_apply),
            ("Create profile backup before apply", self._var_backup),
            ("Scan file conflicts after optimize", self._var_scan),
            ("Auto-resolve via xEdit patch",       self._var_resolve),
        ]:
            ttk.Checkbutton(body_opts, text=text, variable=var,
                            style="TCheckbutton").pack(anchor=tk.W, pady=1)

        _, body_paths = self._section(inner, "Paths")
        for label, sv in [("Patch Name", self._sv_patch),
                           ("xEdit Path", self._sv_xedit_p)]:
            row = tk.Frame(body_paths, background=PALETTE["bg_panel"])
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=label, width=12, anchor=tk.W,
                     bg=PALETTE["bg_panel"], fg=PALETTE["text_dim"],
                     font=_FONT_UI).pack(side=tk.LEFT)
            ttk.Entry(row, textvariable=sv, font=_FONT_UI).pack(
                side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))
            if label == "xEdit Path":
                ttk.Button(row, text="Browse…",
                           command=lambda: self._browse_xedit()).pack(
                    side=tk.LEFT, padx=(4, 0))

        _, body_det = self._section(inner, "Detected Paths")
        self._txt_detected = self._scrolled_text(body_det, height=5)

        return tab

    def _build_status_bar(self, parent: tk.Widget) -> None:
        bar = tk.Frame(parent, background=PALETTE["bg_header"], height=22)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        bar.pack_propagate(False)

        self._dot = tk.Label(bar, text="●", bg=PALETTE["bg_header"],
                             fg="#666666", font=_FONT_SMALL)
        self._dot.pack(side=tk.LEFT, padx=(8, 2), pady=2)
        tk.Label(bar, textvariable=self._sv_status,
                 bg=PALETTE["bg_header"], fg=PALETTE["text_dim"],
                 font=_FONT_SMALL).pack(side=tk.LEFT, pady=2)

        self._sv_sb_count = tk.StringVar(value="0 plugins")
        self._sv_sb_issues = tk.StringVar(value="No issues")
        tk.Label(bar, text="|", bg=PALETTE["bg_header"], fg="#444").pack(
            side=tk.LEFT, padx=8, pady=2)
        tk.Label(bar, textvariable=self._sv_sb_count,
                 bg=PALETTE["bg_header"], fg=PALETTE["text_dim"],
                 font=_FONT_SMALL).pack(side=tk.LEFT)
        tk.Label(bar, text="|", bg=PALETTE["bg_header"], fg="#444").pack(
            side=tk.LEFT, padx=8, pady=2)
        tk.Label(bar, textvariable=self._sv_sb_issues,
                 bg=PALETTE["bg_header"], fg=PALETTE["text_dim"],
                 font=_FONT_SMALL).pack(side=tk.LEFT)

    # ------------------------------------------------------------------
    # Text widget helpers
    # ------------------------------------------------------------------

    def _set_text(self, widget: tk.Text, content: str) -> None:
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, content)
        widget.configure(state=tk.DISABLED)

    def _set_status(self, msg: str, colour: str = PALETTE["text_dim"]) -> None:
        self._sv_status.set(msg)
        self._dot.configure(fg=colour)

    # ------------------------------------------------------------------
    # Backend helpers
    # ------------------------------------------------------------------

    def _get_mo2(self) -> Any:
        if not self._backend:
            return None
        MO2 = self._backend["MO2Integration"]

        # 1. Use override if provided (from command line or manual browse)
        if self._mo2_path_override:
            return MO2(Path(self._mo2_path_override), game_name='Fallout 4')

        # 2. Try auto-detection
        detected = MO2.detect_mo2_installation()
        if detected:
            return MO2(detected, game_name='Fallout 4')

        # 3. Try loading from saved config
        try:
            config_file = Path.home() / ".mossy_manager" / "config.yaml"
            if config_file.exists():
                import yaml
                config = yaml.safe_load(config_file.read_text())
                if config and 'mo2_path' in config:
                    saved_path = Path(config['mo2_path'])
                    if saved_path.exists() and (saved_path / "ModOrganizer.exe").exists():
                        return MO2(saved_path, game_name='Fallout 4')
        except Exception:
            pass

        return None

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_profile_change(self) -> None:
        self._refresh_load_order()

    def _browse_xedit(self) -> None:
        path = filedialog.askopenfilename(
            title="Select xEdit executable",
            filetypes=[("Executables", "*.exe"), ("All files", "*.*")],
        )
        if path:
            self._sv_xedit_p.set(path)

    def _browse_mo2_path(self) -> None:
        """Browse for MO2 installation directory."""
        path = filedialog.askdirectory(
            title="Select Mod Organizer 2 Installation Folder",
            mustexist=True
        )
        if path:
            mo2_path = Path(path)

            # Verify it's a valid MO2 installation
            mo2_exe = mo2_path / "ModOrganizer.exe"
            if not mo2_exe.exists():
                messagebox.showerror(
                    "Invalid MO2 Path",
                    f"ModOrganizer.exe not found in:\n{mo2_path}\n\n"
                    f"Please select the folder containing ModOrganizer.exe"
                )
                return

            # Save to config
            try:
                config_dir = Path.home() / ".mossy_manager"
                config_dir.mkdir(parents=True, exist_ok=True)
                config_file = config_dir / "config.yaml"

                import yaml
                if config_file.exists():
                    config = yaml.safe_load(config_file.read_text()) or {}
                else:
                    config = {}

                config['mo2_path'] = str(mo2_path)
                config_file.write_text(yaml.dump(config))

                # Update override and reload
                self._mo2_path_override = str(mo2_path)
                self._mo2 = None  # Clear cached MO2 instance

                messagebox.showinfo(
                    "MO2 Path Set",
                    f"MO2 path set to:\n{mo2_path}\n\nReloading..."
                )

                # Reload MO2 info
                self._load_mo2_info()

            except Exception as e:
                messagebox.showerror(
                    "Failed to Save",
                    f"Could not save MO2 path to config:\n{e}"
                )

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        for btn in (self._btn_optimize, self._btn_conflicts,
                    self._btn_refresh, self._btn_merge):
            btn.configure(state=state)
        cursor = "watch" if busy else ""
        self._root.configure(cursor=cursor)

    # ------------------------------------------------------------------
    # Async (threaded) operations
    # ------------------------------------------------------------------

    def _run_in_thread(self, func, *args) -> None:
        """Run *func* in a background thread; re-enable UI when done."""
        self._set_busy(True)

        def _worker():
            try:
                func(*args)
            finally:
                self._root.after(0, lambda: self._set_busy(False))

        threading.Thread(target=_worker, daemon=True).start()

    # ------------------------------------------------------------------
    # Load MO2 info
    # ------------------------------------------------------------------

    def _load_mo2_info(self) -> None:
        def _do():
            mo2 = self._get_mo2()
            if mo2 is None:
                self._root.after(0, lambda: (
                    self._sv_mo2_path.set("MO2 not found"),
                    self._set_status("MO2 not found", PALETTE["danger"]),
                ))
                return
            self._mo2 = mo2
            profiles = mo2.list_profiles() or []
            self._profiles = profiles
            path_text = f"MO2: {mo2.mo2_path}" if mo2.mo2_path else "MO2 detected"

            # xEdit detection
            xedit_text = "xEdit: not found"
            try:
                from mossy_manager.utils.xedit_integration import XEditIntegration
                xe = XEditIntegration()
                search = [mo2.mo2_path] if mo2.mo2_path else []
                xep = xe.detect_xedit("fallout4", search_roots=search) if search else xe.detect_xedit("fallout4")
                if xep:
                    xedit_text = f"xEdit: {xep}"
                    det = (f"MO2 Path  : {mo2.mo2_path or '(unknown)'}\n"
                           f"Mods Path : {mo2.mods_path or '(unknown)'}\n"
                           f"xEdit Path: {xep}")
                    self._root.after(0, lambda t=det: self._set_text(self._txt_detected, t))
            except Exception:
                pass

            def _update():
                self._sv_mo2_path.set(path_text)
                self._sv_xedit.set(xedit_text)
                self._profile_cb["values"] = profiles
                if profiles:
                    self._sv_profile.set(profiles[0])
                    self._refresh_load_order()
                self._set_status("Ready", PALETTE["success"])

            self._root.after(0, _update)

        self._run_in_thread(_do)

    # ------------------------------------------------------------------
    # Load order
    # ------------------------------------------------------------------

    def _refresh_load_order(self) -> None:
        profile = self._sv_profile.get()
        if not profile or not self._mo2:
            return

        def _do():
            try:
                lo = self._mo2.read_loadorder_txt(profile) or []
                en = self._mo2.read_plugins_txt(profile) or {}
                self._load_order = lo
                self._enabled = en
                self._root.after(0, lambda: self._render_plugins(lo, en))
                self._root.after(0, lambda: self._set_status(
                    f"Loaded {len(lo)} plugins", PALETTE["success"]))
            except Exception as exc:
                self._root.after(0, lambda: (
                    self._set_status(str(exc), PALETTE["danger"]),
                    messagebox.showerror("Load order error", str(exc)),
                ))

        self._run_in_thread(_do)

    def _render_plugins(self, load_order: List[str],
                        enabled: Dict[str, bool]) -> None:
        for item in self._tree.get_children():
            self._tree.delete(item)

        for idx, name in enumerate(load_order):
            lower = name.lower()
            if lower.endswith(".esm"):
                type_tag, type_label = "esm_tag", "ESM"
            elif lower.endswith(".esl"):
                type_tag, type_label = "esl_tag", "ESL"
            else:
                type_tag, type_label = "esp_tag", "ESP"

            is_on = enabled.get(name, True)
            row_tag = "even" if idx % 2 == 0 else "odd"
            self._tree.insert("", tk.END,
                              values=(idx + 1, "✓" if is_on else "✗",
                                      name, type_label),
                              tags=(row_tag, type_tag))

        count = len(load_order)
        self._lbl_count.configure(text=str(count))
        self._sv_sb_count.set(f"{count} plugins")

    # ------------------------------------------------------------------
    # Optimize
    # ------------------------------------------------------------------

    def _run_optimize(self) -> None:
        profile = self._sv_profile.get()
        if not profile or not self._mo2:
            messagebox.showwarning("No profile", "Select an MO2 profile first.")
            return

        def _do():
            try:
                self._root.after(0, lambda: self._set_status(
                    "Optimizing…", PALETTE["warn"]))
                lo = self._mo2.read_loadorder_txt(profile)
                if not lo:
                    raise ValueError("No plugins found in profile")

                rules = self._backend["Fallout4Rules"]
                issues = rules.validate_load_order(lo)

                # Get Data path for reading plugin dependencies
                data_path = self._mo2.get_game_data_path() if hasattr(self._mo2, 'get_game_data_path') else None
                optimized = rules.optimize_load_order(lo, data_path=data_path)
                recommendations = rules.get_recommendations(optimized)

                # Store optimized order for later application
                self._last_optimized = optimized

                errors   = len(issues.get("errors",   []))
                warnings = len(issues.get("warnings", []))
                recs     = len(recommendations)

                preview = "\n".join(
                    f"{i+1:3}. {p}" for i, p in enumerate(optimized[:40])
                )
                if len(optimized) > 40:
                    preview += f"\n    … and {len(optimized) - 40} more"

                applied = False  # Track if we applied automatically
                if self._var_apply.get():
                    if self._var_backup.get():
                        prof_path = self._mo2.get_profile_path(profile)
                        if prof_path:
                            ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
                            shutil.copytree(prof_path, prof_path.parent /
                                            f"{profile}_backup_{ts}")
                    plugins_enabled = self._mo2.read_plugins_txt(profile)
                    self._mo2.write_plugins_txt(
                        profile, {p: plugins_enabled.get(p, True) for p in optimized})
                    self._mo2.write_loadorder_txt(profile, optimized)
                    status_msg = "Applied"
                    applied = True
                else:
                    status_msg = "Preview (dry-run)"

                rec_text = "\n".join(recommendations) if recommendations else "None"

                def _update():
                    self._sv_stat_status.set(status_msg)
                    self._sv_stat_err.set(str(errors))
                    self._sv_stat_warn.set(str(warnings))
                    self._sv_stat_rec.set(str(recs))
                    self._set_text(self._txt_results, preview)
                    self._set_text(self._txt_recs, rec_text)
                    self._set_text(self._txt_ai,
                                   rec_text if rec_text != "None"
                                   else "No AI recommendations.")
                    self._sv_sb_issues.set(
                        f"{errors} errors, {warnings} warnings")
                    self._set_status(
                        status_msg,
                        PALETTE["success"] if not errors else PALETTE["warn"])
                    # Show "Apply Load Order" button if we didn't auto-apply
                    if not applied:
                        self._apply_button_frame.pack(fill=tk.X, pady=(6, 0))
                    else:
                        self._apply_button_frame.pack_forget()
                    self._notebook.select(0)
                    self._refresh_load_order()

                self._root.after(0, _update)

            except Exception as exc:
                self._root.after(0, lambda: (
                    self._set_status(str(exc), PALETTE["danger"]),
                    messagebox.showerror("Optimize error", str(exc)),
                ))

        self._run_in_thread(_do)

    def _apply_last_optimization(self) -> None:
        """Apply the last calculated optimized load order"""
        if not self._last_optimized:
            messagebox.showwarning("No Optimization", "No optimized load order to apply. Run optimization first.")
            return

        profile = self._sv_profile.get()
        if not profile or not self._mo2:
            messagebox.showwarning("No profile", "Select an MO2 profile first.")
            return

        # Confirm with user
        msg = (
            f"Apply optimized load order with {len(self._last_optimized)} plugins?\n\n"
            f"This will:\n"
            f"• Create a backup of your current profile\n"
            f"• Update loadorder.txt and plugins.txt\n"
            f"• Preserve enabled/disabled state of plugins\n\n"
            f"Continue?"
        )
        if not messagebox.askyesno("Confirm Apply", msg):
            return

        def _do():
            try:
                self._root.after(0, lambda: self._set_status(
                    "Applying load order…", PALETTE["warn"]))

                # Create backup
                prof_path = self._mo2.get_profile_path(profile)
                backup_name = "(unknown)"
                if prof_path:
                    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
                    backup_path = prof_path.parent / f"{profile}_backup_{ts}"
                    shutil.copytree(prof_path, backup_path)
                    backup_name = backup_path.name
                    logger.info(f"Created backup: {backup_path}")

                # Apply the load order
                plugins_enabled = self._mo2.read_plugins_txt(profile)
                optimized_plugins = {p: plugins_enabled.get(p, True) for p in self._last_optimized}

                self._mo2.write_plugins_txt(profile, optimized_plugins)
                self._mo2.write_loadorder_txt(profile, self._last_optimized)

                self._root.after(0, lambda bn=backup_name: (
                    self._set_status("Load order applied successfully", PALETTE["success"]),
                    self._sv_stat_status.set("Applied"),
                    self._apply_button_frame.pack_forget(),  # Hide button after applying
                    self._refresh_load_order(),
                    messagebox.showinfo("Success",
                        f"Load order applied successfully!\n\n"
                        f"Backup created at:\n{bn}")
                ))

            except Exception as exc:
                logger.error(f"Error applying load order: {exc}", exc_info=True)
                self._root.after(0, lambda e=str(exc): (
                    self._set_status(f"Error: {e}", PALETTE["danger"]),
                    messagebox.showerror("Apply Error", f"Failed to apply load order:\n\n{e}")
                ))

        self._run_in_thread(_do)

    # ------------------------------------------------------------------
    # Scan conflicts
    # ------------------------------------------------------------------

    def _run_scan_conflicts(self) -> None:
        if not self._mo2:
            messagebox.showwarning("No MO2", "MO2 not detected.")
            return

        def _do():
            try:
                self._root.after(0, lambda: self._set_status(
                    "Scanning conflicts…", PALETTE["warn"]))
                mods_path = self._mo2.mods_path
                if not mods_path or not Path(mods_path).exists():
                    raise ValueError("Mods directory not found")

                Resolver = self._backend["ConflictResolver"]
                resolver = Resolver(Path(mods_path))
                scanned = 0
                for mod_dir in Path(mods_path).iterdir():
                    if mod_dir.is_dir():
                        resolver.scan_mod_files(mod_dir.name, mod_dir)
                        scanned += 1

                stats = resolver.get_statistics()
                report_lines = [
                    f"{scanned} mods scanned.",
                    f"Critical : {stats.get('critical', 0)}",
                    f"High     : {stats.get('high', 0)}",
                    f"Medium   : {stats.get('medium', 0)}",
                    f"Low      : {stats.get('low', 0)}",
                ]
                dot_colour = (PALETTE["danger"]
                              if stats.get("critical") or stats.get("high")
                              else PALETTE["success"])

                def _update():
                    self._sv_cs_mods.set(str(scanned))
                    self._sv_cs_critical.set(str(stats.get("critical", 0)))
                    self._sv_cs_high.set(str(stats.get("high", 0)))
                    self._sv_cs_medium.set(str(stats.get("medium", 0)))
                    self._sv_cs_low.set(str(stats.get("low", 0)))
                    self._set_text(self._txt_conflicts, "\n".join(report_lines))
                    self._set_status("Conflict scan complete", dot_colour)
                    self._notebook.select(1)

                self._root.after(0, _update)

            except Exception as exc:
                self._root.after(0, lambda: (
                    self._set_status(str(exc), PALETTE["danger"]),
                    messagebox.showerror("Conflict scan error", str(exc)),
                ))

        self._run_in_thread(_do)

    # ------------------------------------------------------------------
    # Merge wizard (modal dialog)
    # ------------------------------------------------------------------

    def _open_merge_dialog(self) -> None:
        if not self._mo2:
            messagebox.showwarning("No MO2", "MO2 not detected.")
            return

        mods_path = self._mo2.mods_path
        if not mods_path or not Path(mods_path).exists():
            messagebox.showwarning("No mods directory", "Mods directory not found.")
            return

        mods = sorted(p.name for p in Path(mods_path).iterdir() if p.is_dir())

        dlg = tk.Toplevel(self._root)
        dlg.title("Merge Mods")
        dlg.geometry("460x420")
        dlg.configure(background=PALETTE["bg_panel"])
        dlg.resizable(False, False)
        dlg.transient(self._root)
        dlg.grab_set()

        # Header
        hdr = tk.Frame(dlg, background=PALETTE["bg_header"], height=28)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Merge Mods",
                 bg=PALETTE["bg_header"], fg=PALETTE["text_head"],
                 font=_FONT_HEAD).pack(side=tk.LEFT, padx=10, pady=5)

        # Body
        body = tk.Frame(dlg, background=PALETTE["bg_panel"])
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        tk.Label(body, text="Select mods to merge:",
                 bg=PALETTE["bg_panel"], fg=PALETTE["text_dim"],
                 font=_FONT_SMALL).pack(anchor=tk.W)

        list_frame = tk.Frame(body, background=PALETTE["bg_dark"],
                              relief="flat", bd=1,
                              highlightbackground=PALETTE["border"],
                              highlightthickness=1)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=4)

        lb = tk.Listbox(list_frame, selectmode=tk.MULTIPLE,
                        bg=PALETTE["bg_dark"], fg=PALETTE["text"],
                        selectbackground=PALETTE["bg_row_sel"],
                        selectforeground=PALETTE["text_head"],
                        font=_FONT_UI, relief="flat",
                        activestyle="dotbox",
                        highlightthickness=0)
        lsb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=lb.yview)
        lb.configure(yscrollcommand=lsb.set)
        lsb.pack(side=tk.RIGHT, fill=tk.Y)
        lb.pack(fill=tk.BOTH, expand=True)
        for m in mods:
            lb.insert(tk.END, m)

        self._sv_merge_status = tk.StringVar()
        lbl_result = tk.Label(body, textvariable=self._sv_merge_status,
                              bg=PALETTE["bg_panel"], fg=PALETTE["success"],
                              font=_FONT_SMALL, wraplength=420)
        lbl_result.pack(anchor=tk.W, pady=2)

        # Footer
        footer = tk.Frame(dlg, background=PALETTE["bg_panel"],
                          relief="flat",
                          highlightbackground=PALETTE["border"],
                          highlightthickness=1)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        def _do_merge():
            sel = lb.curselection()
            if not sel:
                messagebox.showwarning("No selection", "Select at least one mod.")
                return
            chosen = [lb.get(i) for i in sel]

            # Basic merge implementation: create a new merged mod folder
            try:
                if not self._backend or not self._mo2:
                    self._sv_merge_status.set("Error: MO2 not detected")
                    return

                mods_dir = self._mo2.mods_path
                if not mods_dir or not Path(str(mods_dir)).exists():
                    self._sv_merge_status.set("Error: Mods directory not found")
                    return

                # Create merged mod name
                merge_name = f"MossyMerge_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
                merge_path = Path(str(mods_dir)) / merge_name

                # Create merge directory
                merge_path.mkdir(parents=True, exist_ok=True)

                # Copy files from each selected mod to the merged mod
                total_files = 0
                for mod_name in chosen:
                    mod_path = Path(str(mods_dir)) / mod_name
                    if not mod_path.exists():
                        continue

                    # Copy all files from this mod to the merge (simple file copy)
                    import shutil
                    for item in mod_path.rglob('*'):
                        if item.is_file():
                            rel_path = item.relative_to(mod_path)
                            dest = merge_path / rel_path
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(item, dest)
                            total_files += 1

                # Create a metadata file
                meta_file = merge_path / "meta.ini"
                meta_content = (
                    "[General]\n"
                    f"version=1.0\n"
                    f"installationFile={merge_name}\n"
                    f"comments=Merged mod created by Mossy Manager from: {', '.join(chosen)}\n"
                    f"created={datetime.now(timezone.utc).isoformat()}\n"
                )
                meta_file.write_text(meta_content, encoding='utf-8')

                self._sv_merge_status.set(
                    f"✓ Merge complete: {merge_name} ({total_files} files from {len(chosen)} mods)"
                )
                dlg.destroy()

            except Exception as e:
                logger.exception(f"Merge error: {e}")
                self._sv_merge_status.set(f"Merge failed: {str(e)}")


        ttk.Button(footer, text="⊕ Merge", style="Primary.TButton",
                   command=_do_merge).pack(side=tk.RIGHT, padx=6, pady=6)
        ttk.Button(footer, text="Cancel",
                   command=dlg.destroy).pack(side=tk.RIGHT, padx=0, pady=6)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start the event loop (blocks until the window is closed)."""
        # Load backend data after the window is shown
        self._root.after(200, self._load_mo2_info)
        self._root.after(100, lambda: (
            self._set_text(self._txt_results,
                           'Run "Optimize" to see the proposed load order changes.'),
            self._set_text(self._txt_conflicts, "No scan run yet."),
            self._set_text(self._txt_ai,
                           "Run Optimize to get AI-powered recommendations."),
        ))

        # Version
        if self._backend:
            ver = self._backend.get("version", "1.0.0")
            self._sv_version.set(f"v{ver}")

        self._root.mainloop()


# ---------------------------------------------------------------------------
# Module-level launch function (called by the CLI)
# ---------------------------------------------------------------------------

def launch(mo2_path: Optional[str] = None) -> None:
    """
    Launch the self-contained desktop GUI.

    This is the authoritative entry point for *mossy ui*.  It MUST NOT start
    a web server.  See UI_MANIFEST at the repository root.
    """
    if not _TKINTER_AVAILABLE:  # pragma: no cover
        raise RuntimeError(
            "tkinter is not available. "
            "Install python3-tk (Linux) or use a full Python distribution (Windows/macOS)."
        )
    app = DesktopApp(mo2_path=mo2_path)
    app.run()
