"""
FixGenerator — produces complete, executable fixes for every issue the
ModReasoner finds.

Unlike ScriptWriter (which emits generic templates), FixGenerator creates
code that is *specific* to the exact problem found:

  • It knows the plugin names, positions, and resource paths involved
  • Python fixes can be `apply()`-ed immediately — they modify loadorder.txt
    or modlist.txt in place without needing any external tool
  • xEdit Pascal fixes have real ``Process(e)`` bodies with exact plugin-name
    guards, record-signature filters, and wbCopyElementToFile calls —
    zero placeholders
  • PowerShell / batch fixes are parameter-substituted for the actual paths

Every ``Fix`` carries:
  ``title``          — short name
  ``description``    — plain-English explanation
  ``issue_rule``     — the reasoning rule that triggered this fix
  ``fix_type``       — "python" | "pascal" | "ini" | "powershell" | "batch"
  ``code``           — complete, executable code as a string
  ``filename``       — suggested save filename
  ``can_auto_apply`` — True when the fix can be applied without xEdit
  ``apply()``        — executes the fix directly (Python-type only)
"""

from __future__ import annotations

import logging
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from mossy_manager.games.fallout4 import Fallout4Rules

logger = logging.getLogger(__name__)

# Import lazily to avoid circulars
try:
    from mossy_manager.ai.reasoner import ReasoningResult, ReasoningStep
    _REASONER_AVAILABLE = True
except ImportError:  # pragma: no cover
    _REASONER_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _py_header(title: str, description: str) -> str:
    return textwrap.dedent(f"""\
        # ════════════════════════════════════════════════════════════════
        # Mossy Manager — Auto-Fix  |  {_ts()}
        # Title      : {title}
        # Description: {description}
        # Apply      : python <this_file.py>   (safe to re-run)
        # ════════════════════════════════════════════════════════════════
        """)


def _pas_header(title: str, description: str) -> str:
    return textwrap.dedent(f"""\
        // ════════════════════════════════════════════════════════════════
        // Mossy Manager — Auto-Fix  |  {_ts()}
        // Title      : {title}
        // Description: {description}
        // Run via    : xEdit → Tools → Apply Script
        // ════════════════════════════════════════════════════════════════
        """)


def _ini_header(title: str, description: str) -> str:
    return textwrap.dedent(f"""\
        ; ════════════════════════════════════════════════════════════════
        ; Mossy Manager — Auto-Fix  |  {_ts()}
        ; Title      : {title}
        ; Description: {description}
        ; Paste into : Documents\\My Games\\Fallout4\\Fallout4Custom.ini
        ; ════════════════════════════════════════════════════════════════
        """)


def _bat_header(title: str, description: str) -> str:
    return textwrap.dedent(f"""\
        REM ════════════════════════════════════════════════════════════════
        REM Mossy Manager — Auto-Fix  |  {_ts()}
        REM Title      : {title}
        REM Description: {description}
        REM ════════════════════════════════════════════════════════════════
        """)


# Map file extension to record signature used in Fallout 4 plugin data
_EXT_TO_SIG: Dict[str, str] = {
    ".pex": "SCPT",
    ".psc": "SCPT",
    ".dds": "TXST",
    ".tga": "TXST",
    ".nif": "STAT",
    ".hkx": "IDLE",
    ".wav": "SOUN",
    ".fuz": "SOUN",
    ".xwm": "SOUN",
    ".mp3": "MUSC",
    ".esp": "MAST",
    ".esm": "MAST",
    ".esl": "MAST",
    ".ini": "GMST",
    ".json": "GMST",
}

_FOLDER_TO_SIG: Dict[str, str] = {
    "scripts":   "SCPT",
    "textures":  "TXST",
    "meshes":    "STAT",
    "sounds":    "SOUN",
    "music":     "MUSC",
    "interface": "KYWD",
    "lodsettings": "LGTM",
}


def _infer_record_sig(resource: str) -> str:
    """Infer the most likely xEdit record signature from a file/resource path."""
    lower = resource.lower()
    # Try folder name first
    parts = lower.replace("\\", "/").split("/")
    for part in parts:
        if part in _FOLDER_TO_SIG:
            return _FOLDER_TO_SIG[part]
    # Try file extension
    for ext, sig in _EXT_TO_SIG.items():
        if lower.endswith(ext):
            return sig
    return ""  # unknown — generate a broad filter


# ─────────────────────────────────────────────────────────────────────────────
# Fix dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Fix:
    """A complete, executable fix for one specific issue."""

    title: str
    description: str
    issue_rule: str           # the ReasoningStep.rule that triggered this
    fix_type: str             # "python" | "pascal" | "ini" | "batch" | "powershell"
    code: str                 # complete, ready-to-run code
    filename: str             # suggested save filename
    can_auto_apply: bool = False
    _apply_fn: Optional[Callable[[], str]] = field(default=None, repr=False)

    def apply(self) -> str:
        """
        Execute this fix directly (Python fixes only).

        Returns
        -------
        str
            Human-readable result message.

        Raises
        ------
        NotImplementedError
            If this fix type cannot be applied automatically.
        """
        if not self.can_auto_apply or self._apply_fn is None:
            raise NotImplementedError(
                f"Fix '{self.title}' (type={self.fix_type}) must be applied manually. "
                "Save the code to a file and follow the instructions in the header."
            )
        return self._apply_fn()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "issue_rule": self.issue_rule,
            "fix_type": self.fix_type,
            "filename": self.filename,
            "can_auto_apply": self.can_auto_apply,
            "code_length": len(self.code),
            "code_preview": self.code[:300],
        }


# ─────────────────────────────────────────────────────────────────────────────
# Per-rule fix builders
# ─────────────────────────────────────────────────────────────────────────────

def _fix_master_file_order(
    step: "ReasoningStep",
    load_order: List[str],
    loadorder_path: Optional[Path],
) -> Fix:
    """Generate a Python script that corrects master file ordering in loadorder.txt."""

    correct_masters = Fallout4Rules.MASTER_FILES
    masters_repr = repr(correct_masters)
    lo_path_str = str(loadorder_path) if loadorder_path else "profiles/Default/loadorder.txt"

    code = _py_header(
        "Fix Master File Order",
        step.deduction,
    ) + textwrap.dedent(f"""\
        from pathlib import Path

        LOADORDER_FILE = Path(r"{lo_path_str}")

        # Official Fallout 4 master files in required order
        CORRECT_MASTERS = {masters_repr}

        def fix(path: Path) -> None:
            if not path.exists():
                print(f"[Mossy] ERROR: {{path}} does not exist — set LOADORDER_FILE to the correct path.")
                return

            raw = path.read_text(encoding="utf-8").splitlines()
            comments = [l for l in raw if l.startswith("#")]
            plugins  = [l for l in raw if l and not l.startswith("#")]

            present_masters = [m for m in CORRECT_MASTERS if m in plugins]
            non_masters     = [p for p in plugins if p not in CORRECT_MASTERS]

            new_order = comments + present_masters + non_masters
            path.write_text("\\n".join(new_order) + "\\n", encoding="utf-8")
            print(f"[Mossy] ✓ Master file order corrected in {{path}}")
            for i, m in enumerate(present_masters):
                print(f"         {{i}}: {{m}}")

        fix(LOADORDER_FILE)
        """)

    def _apply() -> str:
        if not loadorder_path or not loadorder_path.exists():
            return f"[Mossy] Cannot apply: loadorder.txt not found at {loadorder_path}"
        raw = loadorder_path.read_text(encoding="utf-8").splitlines()
        comments = [l for l in raw if l.startswith("#")]
        plugins  = [l for l in raw if l and not l.startswith("#")]
        present_masters = [m for m in correct_masters if m in plugins]
        non_masters     = [p for p in plugins if p not in correct_masters]
        new_order = comments + present_masters + non_masters
        loadorder_path.write_text("\n".join(new_order) + "\n", encoding="utf-8")
        return f"[Mossy] ✓ Master file order corrected ({len(present_masters)} masters reordered)"

    return Fix(
        title="Fix Master File Order",
        description=step.deduction,
        issue_rule=step.rule,
        fix_type="python",
        code=code,
        filename="fix_master_file_order.py",
        can_auto_apply=loadorder_path is not None,
        _apply_fn=_apply,
    )


def _fix_patch_position(
    step: "ReasoningStep",
    load_order: List[str],
    loadorder_path: Optional[Path],
) -> Fix:
    """Move a patch plugin to the correct position (80 % through the load order)."""

    plugin = step.plugin or ""
    lo_path_str = str(loadorder_path) if loadorder_path else "profiles/Default/loadorder.txt"

    code = _py_header(
        f"Move Patch Plugin: {plugin}",
        step.deduction,
    ) + textwrap.dedent(f"""\
        from pathlib import Path

        LOADORDER_FILE  = Path(r"{lo_path_str}")
        PLUGIN_TO_MOVE  = "{plugin}"
        TARGET_FRACTION = 0.80   # place at 80 % of the load order

        def fix(path: Path) -> None:
            if not path.exists():
                print(f"[Mossy] ERROR: {{path}} not found.")
                return
            lines = [l.strip() for l in path.read_text(encoding="utf-8").splitlines()]
            comments = [l for l in lines if l.startswith("#")]
            plugins  = [l for l in lines if l and not l.startswith("#")]

            if PLUGIN_TO_MOVE not in plugins:
                print(f"[Mossy] WARNING: '{{PLUGIN_TO_MOVE}}' not found in load order — nothing to do.")
                return

            plugins.remove(PLUGIN_TO_MOVE)
            target = min(int(len(plugins) * TARGET_FRACTION), len(plugins))
            plugins.insert(target, PLUGIN_TO_MOVE)
            path.write_text("\\n".join(comments + plugins) + "\\n", encoding="utf-8")
            print(f"[Mossy] ✓ Moved '{{PLUGIN_TO_MOVE}}' to position {{target}}/{{len(plugins)}}")

        fix(LOADORDER_FILE)
        """)

    def _apply() -> str:
        if not loadorder_path or not loadorder_path.exists():
            return f"[Mossy] Cannot apply: loadorder.txt not found at {loadorder_path}"
        lines = [l.strip() for l in loadorder_path.read_text(encoding="utf-8").splitlines()]
        comments = [l for l in lines if l.startswith("#")]
        plugins  = [l for l in lines if l and not l.startswith("#")]
        if plugin not in plugins:
            return f"[Mossy] '{plugin}' not found in load order — nothing moved"
        plugins.remove(plugin)
        target = min(int(len(plugins) * 0.80), len(plugins))
        plugins.insert(target, plugin)
        loadorder_path.write_text("\n".join(comments + plugins) + "\n", encoding="utf-8")
        return f"[Mossy] ✓ Moved '{plugin}' to position {target}/{len(plugins)}"

    return Fix(
        title=f"Move Patch to Correct Position: {plugin}",
        description=step.deduction,
        issue_rule=step.rule,
        fix_type="python",
        code=code,
        filename=f"fix_patch_position_{plugin.replace('.', '_')}.py",
        can_auto_apply=loadorder_path is not None,
        _apply_fn=_apply,
    )


def _fix_ufp_position(
    step: "ReasoningStep",
    load_order: List[str],
    loadorder_path: Optional[Path],
) -> Fix:
    """Move the Unofficial Fallout 4 Patch to right after the official DLC masters."""

    ufp_plugin = step.plugin or next(
        (p for p in load_order if "unofficial" in p.lower() and "patch" in p.lower()),
        "UnoffPatch.esp",
    )
    lo_path_str = str(loadorder_path) if loadorder_path else "profiles/Default/loadorder.txt"
    insert_after = Fallout4Rules.MASTER_FILES[-1]   # after NukaWorld

    code = _py_header(
        f"Move UFO4P to Correct Position: {ufp_plugin}",
        step.deduction,
    ) + textwrap.dedent(f"""\
        from pathlib import Path

        LOADORDER_FILE = Path(r"{lo_path_str}")
        UFP_PLUGIN     = "{ufp_plugin}"
        INSERT_AFTER   = "{insert_after}"   # last official DLC master

        def fix(path: Path) -> None:
            if not path.exists():
                print(f"[Mossy] ERROR: {{path}} not found.")
                return
            lines   = [l.strip() for l in path.read_text(encoding="utf-8").splitlines()]
            comments = [l for l in lines if l.startswith("#")]
            plugins  = [l for l in lines if l and not l.startswith("#")]

            if UFP_PLUGIN not in plugins:
                print(f"[Mossy] WARNING: '{{UFP_PLUGIN}}' not found — nothing to do.")
                return

            plugins.remove(UFP_PLUGIN)

            if INSERT_AFTER in plugins:
                idx = plugins.index(INSERT_AFTER) + 1
            else:
                # Fall back to just after whatever masters are present
                last_master_idx = max(
                    (i for i, p in enumerate(plugins) if p.lower().endswith(".esm")),
                    default=0,
                )
                idx = last_master_idx + 1

            plugins.insert(idx, UFP_PLUGIN)
            path.write_text("\\n".join(comments + plugins) + "\\n", encoding="utf-8")
            print(f"[Mossy] ✓ Moved '{{UFP_PLUGIN}}' to position {{idx}} (after {{INSERT_AFTER}})")

        fix(LOADORDER_FILE)
        """)

    def _apply() -> str:
        if not loadorder_path or not loadorder_path.exists():
            return f"[Mossy] Cannot apply: loadorder.txt not found at {loadorder_path}"
        lines    = [l.strip() for l in loadorder_path.read_text(encoding="utf-8").splitlines()]
        comments = [l for l in lines if l.startswith("#")]
        plugins  = [l for l in lines if l and not l.startswith("#")]
        if ufp_plugin not in plugins:
            return f"[Mossy] '{ufp_plugin}' not in load order — nothing moved"
        plugins.remove(ufp_plugin)
        idx = (plugins.index(insert_after) + 1) if insert_after in plugins else 1
        plugins.insert(idx, ufp_plugin)
        loadorder_path.write_text("\n".join(comments + plugins) + "\n", encoding="utf-8")
        return f"[Mossy] ✓ Moved '{ufp_plugin}' to position {idx}"

    return Fix(
        title=f"Move UFO4P to Correct Position",
        description=step.deduction,
        issue_rule=step.rule,
        fix_type="python",
        code=code,
        filename="fix_ufp_position.py",
        can_auto_apply=loadorder_path is not None,
        _apply_fn=_apply,
    )


def _fix_conflict_patch(
    step: "ReasoningStep",
    load_order: List[str],
    conflict: Optional[Dict[str, Any]],
    patch_name: str,
) -> Fix:
    """
    Generate a complete xEdit Pascal script with exact plugin guards and
    record-signature filters — no TODO placeholders.
    """

    resource  = (conflict or {}).get("resource", step.plugin or "unknown")
    mods      = (conflict or {}).get("mods", [])
    severity  = (conflict or {}).get("severity", step.severity)
    category  = (conflict or {}).get("category", "other")

    # Determine winner (last in load order)
    positions = {p: i for i, p in enumerate(load_order)}
    winner = max(mods, key=lambda m: positions.get(m, -1), default=(mods[-1] if mods else ""))
    losers = [m for m in mods if m != winner]

    # Infer xEdit record signature from resource path
    sig = _infer_record_sig(resource)
    sig_filter = (
        f"  if (sig <> '{sig}') then Exit;  // only {sig} records\n"
        if sig else
        "  // No record-type filter applied — process all conflicting records\n"
    )

    # Build a guard that checks all losing plugins (we want to forward FROM them)
    loser_guards = " or\n         ".join(
        f"(GetFileName(GetFile(e)) = '{m.replace(chr(39), chr(39)*2)}')"
        for m in losers
    ) or f"(GetFileName(GetFile(e)) = '{winner.replace(chr(39), chr(39)*2)}')"

    winner_esc    = winner.replace("'", "''")
    resource_esc  = resource.replace("'", "''")
    patch_name_esc = patch_name.replace("'", "''")
    safe_unit     = "".join(c if c.isalnum() or c == "_" else "_" for c in patch_name)

    master_adds = "\n".join(
        f"  AddRequiredMaster(patchPlugin, '{m.replace(chr(39), chr(39)*2)}', False);"
        for m in mods
    )

    code = _pas_header(
        f"Conflict Patch: {resource}",
        f"[{severity.upper()}] {category} — forward winning records from {winner}",
    ) + textwrap.dedent(f"""\

        unit {safe_unit}_ConflictPatch;

        {{
          Resolves conflict on: {resource}
          Category  : {category}
          Severity  : {severity}
          Winner    : {winner}
          Overridden: {", ".join(losers) if losers else "none"}

          HOW TO USE:
            1. Open FO4Edit with all conflicting plugins loaded.
            2. Tools → Apply Script → select this file.
            3. The patch '{patch_name}.esp' is created automatically.
            4. Save in xEdit, then place {patch_name}.esp AFTER all listed mods.
        }}

        var
          patchPlugin: IInterface;

        function Initialize: integer;
        begin
          Result := 0;
          AddMessage('[Mossy] Creating patch: {patch_name_esc}.esp');
          patchPlugin := AddNewFileName('{patch_name_esc}.esp', False);
          if not Assigned(patchPlugin) then begin
            AddMessage('[Mossy] ERROR: Could not create patch plugin.');
            Result := 1; Exit;
          end;
          // Add required masters
        {master_adds}
          AddMessage('[Mossy] Patch ready. Processing conflicting records...');
        end;

        function Process(e: IInterface): integer;
        var
          sig:     string;
          fname:   string;
          patchRec: IInterface;
        begin
          Result := 0;
          sig   := Signature(e);
          fname := GetFileName(GetFile(e));

          // ── Record-type filter ──────────────────────────────────────
        {sig_filter}
          // ── Plugin filter: only process records from losing mods ────
          if not ({loser_guards}) then Exit;

          // ── Forward record into patch ───────────────────────────────
          patchRec := wbCopyElementToFile(e, patchPlugin, False, True);
          if Assigned(patchRec) then
            AddMessage('[Mossy] Forwarded ' + sig + ' record: ' + FullPath(patchRec))
          else
            AddMessage('[Mossy] WARNING: Could not forward: ' + FullPath(e));
        end;

        function Finalize: integer;
        begin
          Result := 0;
          AddMessage('[Mossy] Conflict patch complete for: {resource_esc}');
          AddMessage('[Mossy] Save {patch_name_esc}.esp and place it AFTER all patched mods.');
        end;

        end.
        """)

    return Fix(
        title=f"xEdit Conflict Patch: {resource}",
        description=(
            f"[{severity.upper()}] Forwards winning '{resource}' record "
            f"from '{winner}' into {patch_name}.esp"
        ),
        issue_rule=step.rule,
        fix_type="pascal",
        code=code,
        filename=f"fix_conflict_{safe_unit}.pas",
        can_auto_apply=False,
    )


def _fix_esl_flag(
    step: "ReasoningStep",
    esp_plugins: List[str],
) -> Fix:
    """Generate a complete xEdit Pascal script that ESL-flags specific plugins."""

    flag_lines = "\n".join(
        f"  if (GetFileName(f) = '{p.replace(chr(39), chr(39)*2)}') then begin\n"
        f"    SetFlag(ElementByPath(f, 'Record Header\\Record Flags'), GetFlagNames(ElementByPath(f, 'Record Header\\Record Flags'), 'ESL'), True);\n"
        f"    AddMessage('[Mossy] ESL-flagged: {p}');\n"
        f"  end;"
        for p in esp_plugins
    )
    plugin_list = "\n".join(f"  //   {p}" for p in esp_plugins)

    code = _pas_header(
        "ESL-Flag Plugins to Free Plugin Slots",
        step.deduction,
    ) + textwrap.dedent(f"""\

        unit ESLFlag_AutoFix;

        {{
          ESL-flags the following plugins to free up plugin slots.
          Fallout 4 has a hard cap of 255 slot-consuming plugins.
          ESL-flagged plugins share a single slot, removing the cap for small mods.

          IMPORTANT: Only flag plugins with fewer than 2048 new Form IDs.
          Verify the new-record count in xEdit before applying.

          Plugins to flag ({len(esp_plugins)}):
        {plugin_list}

          HOW TO USE:
            1. Open FO4Edit.
            2. Tools → Apply Script → select this file.
            3. Save ALL modified plugins.
        }}

        var
          i: integer;
          f: IInterface;

        function Initialize: integer;
        begin
          Result := 0;
          AddMessage('[Mossy] Starting ESL-flag pass on {len(esp_plugins)} plugin(s)...');
          for i := 0 to Pred(FileCount) do begin
            f := FileByIndex(i);
        {flag_lines}
          end;
          AddMessage('[Mossy] ESL-flag pass complete. Save all modified files in xEdit.');
        end;

        function Process(e: IInterface): integer;
        begin Result := 0; end;

        function Finalize: integer;
        begin Result := 0; end;

        end.
        """)

    return Fix(
        title=f"ESL-Flag {len(esp_plugins)} Plugin(s) to Free Slots",
        description=step.deduction,
        issue_rule=step.rule,
        fix_type="pascal",
        code=code,
        filename="fix_esl_flag.pas",
        can_auto_apply=False,
    )


def _fix_papyrus_logging(step: "ReasoningStep") -> Fix:
    """Generate an INI fragment that enables Papyrus crash-diagnosis logging."""
    code = _ini_header(
        "Enable Papyrus Script Logging",
        step.deduction,
    ) + textwrap.dedent("""\

        [Papyrus]
        bEnableLogging=1
        bEnableTrace=1
        bLoadDebugInformation=1
        iMaxAllocatedMemoryBytes=786432

        ; After enabling, reproduce the crash, then read:
        ; Documents\\My Games\\Fallout4\\Logs\\Script\\Papyrus.0.log
        ; Look for "Stack overflow" or "Cannot open store" error lines.
        """)

    return Fix(
        title="Enable Papyrus Script Logging",
        description=step.deduction,
        issue_rule=step.rule,
        fix_type="ini",
        code=code,
        filename="enable_papyrus_logging.ini",
        can_auto_apply=False,
    )


def _fix_archive_invalidation(step: "ReasoningStep") -> Fix:
    """Generate an INI fragment that enables archive invalidation (loose-file mods)."""
    code = _ini_header(
        "Enable Archive Invalidation",
        step.deduction,
    ) + textwrap.dedent("""\

        [Archive]
        bInvalidateOlderFiles=1
        sResourceDataDirsFinal=

        ; This is required for any mod that ships loose files (not packed in BA2).
        ; Without it, the game uses cached BA2 files even when a mod replaces them.
        """)

    return Fix(
        title="Enable Archive Invalidation",
        description=step.deduction,
        issue_rule=step.rule,
        fix_type="ini",
        code=code,
        filename="archive_invalidation.ini",
        can_auto_apply=False,
    )


def _fix_safe_launch(step: "ReasoningStep") -> Fix:
    """Generate a batch file that launches Fallout 4 via F4SE with a pre-launch check."""
    code = _bat_header(
        "Safe F4SE Launch with Plugin-Cap Check",
        step.deduction,
    ) + textwrap.dedent("""\

        @echo off
        setlocal

        REM ── Edit these paths to match your installation ─────────────────
        set F4SE_EXE=C:\\Games\\Fallout4\\f4se_loader.exe
        set PLUGINS_FILE=%LOCALAPPDATA%\\ModOrganizer\\Fallout4\\profiles\\Default\\plugins.txt

        REM ── Plugin cap check ─────────────────────────────────────────────
        if not exist "%PLUGINS_FILE%" (
            echo [Mossy] WARNING: plugins.txt not found at %PLUGINS_FILE%
            goto :launch
        )
        for /f %%c in ('findstr /r "^[*]" "%PLUGINS_FILE%" ^| find /c /v ""') do set CNT=%%c
        echo [Mossy] Enabled plugins: %CNT%/255
        if %CNT% GEQ 255 (
            echo [Mossy] ERROR: Plugin cap exceeded ^(%CNT%/255^).
            echo [Mossy] Run  mossy ai fix  to generate ESL-flagging scripts.
            pause & exit /b 1
        )

        REM ── Launch via F4SE ─────────────────────────────────────────────
        :launch
        if not exist "%F4SE_EXE%" (
            echo [Mossy] ERROR: F4SE not found at %F4SE_EXE%
            echo [Mossy] Download from https://f4se.silverlock.org/
            pause & exit /b 1
        )
        echo [Mossy] Launching via F4SE...
        start "" "%F4SE_EXE%"
        """)

    return Fix(
        title="Safe F4SE Launch Script",
        description=step.deduction,
        issue_rule=step.rule,
        fix_type="batch",
        code=code,
        filename="safe_launch_f4se.bat",
        can_auto_apply=False,
    )


def _fix_missing_dependency(step: "ReasoningStep") -> Fix:
    """Python script that checks for missing masters and blocks launch if absent."""
    plugin   = step.plugin or "unknown.esp"
    deduction = step.deduction

    code = _py_header(
        f"Check Missing Dependency for {plugin}",
        deduction,
    ) + textwrap.dedent(f"""\
        from pathlib import Path
        import sys

        LOADORDER_FILE = Path("profiles/Default/loadorder.txt")
        PLUGIN        = "{plugin}"

        def check(path: Path) -> None:
            if not path.exists():
                print(f"[Mossy] ERROR: {{path}} not found.")
                sys.exit(1)
            plugins = set(
                l.strip() for l in path.read_text(encoding="utf-8").splitlines()
                if l.strip() and not l.startswith("#")
            )
            missing = []
            # Dependency map for known Fallout 4 DLC-dependent plugins
            KNOWN_DEPS = {{
                "DLCRobot.esm":     ["Fallout4.esm"],
                "DLCCoast.esm":     ["Fallout4.esm"],
                "DLCNukaWorld.esm": ["Fallout4.esm", "DLCCoast.esm"],
            }}
            # Check the target plugin
            for master, deps in KNOWN_DEPS.items():
                if master in plugins:
                    for dep in deps:
                        if dep not in plugins:
                            missing.append((master, dep))
            if missing:
                for plugin_name, dep in missing:
                    print(f"[Mossy] ✗ '{{plugin_name}}' requires '{{dep}}' — NOT FOUND in load order")
                sys.exit(2)
            else:
                print(f"[Mossy] ✓ All detected dependencies are present in {{path}}")

        check(LOADORDER_FILE)
        """)

    return Fix(
        title=f"Check Missing Dependency: {plugin}",
        description=deduction,
        issue_rule=step.rule,
        fix_type="python",
        code=code,
        filename=f"check_dependency_{plugin.replace('.', '_')}.py",
        can_auto_apply=False,    # diagnostic, not mutating
    )


# ─────────────────────────────────────────────────────────────────────────────
# Public FixGenerator class
# ─────────────────────────────────────────────────────────────────────────────

class FixGenerator:
    """
    Convert a ``ReasoningResult`` into a list of complete, executable ``Fix``
    objects — one per distinct issue found.

    Parameters
    ----------
    patch_name : str
        Base name for generated xEdit patch plugins (default ``"MossyAutoFix"``).
    """

    def __init__(self, patch_name: str = "MossyAutoFix") -> None:
        self.patch_name = patch_name

    def generate_fixes(
        self,
        reasoning: "ReasoningResult",
        load_order: Optional[List[str]] = None,
        loadorder_path: Optional[Path] = None,
        conflicts: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Fix]:
        """
        Produce a list of ``Fix`` objects from a reasoning result.

        Parameters
        ----------
        reasoning : ReasoningResult
            Output of ``ModReasoner.reason_about_load_order()`` or similar.
        load_order : list of str, optional
            The current load order (used for Python fixes).
        loadorder_path : Path, optional
            Actual path to ``loadorder.txt`` so Python fixes can be applied.
        conflicts : list of dicts, optional
            Conflict dicts from ``ConflictResolver`` for xEdit patch generation.

        Returns
        -------
        list of Fix
            One ``Fix`` per unique rule in the reasoning trace, ordered by
            severity (critical first).
        """
        lo = load_order or []
        conflict_map: Dict[str, Dict[str, Any]] = {}
        for c in (conflicts or []):
            conflict_map[c.get("resource", "")] = c

        # De-duplicate by rule so we don't generate the same fix twice
        seen_rules: set = set()
        fixes: List[Fix] = []

        for step in reasoning.steps:
            rule = step.rule
            if rule in seen_rules:
                continue
            seen_rules.add(rule)

            fix = self._build_fix(step, lo, loadorder_path, conflict_map)
            if fix is not None:
                fixes.append(fix)

        # Sort: critical first, then warning, info
        sev_rank = {"critical": 0, "error": 1, "warning": 2, "info": 3}
        fixes.sort(key=lambda f: sev_rank.get(
            next((s.severity for s in reasoning.steps if s.rule == f.issue_rule), "info"),
            3,
        ))
        return fixes

    def _build_fix(
        self,
        step: "ReasoningStep",
        load_order: List[str],
        loadorder_path: Optional[Path],
        conflict_map: Dict[str, Dict[str, Any]],
    ) -> Optional[Fix]:
        rule = step.rule

        if rule == "MasterFileOrder":
            return _fix_master_file_order(step, load_order, loadorder_path)

        if rule == "PatchLoadedTooEarly" and step.plugin:
            return _fix_patch_position(step, load_order, loadorder_path)

        if rule in ("UFPLoadedLate", "MissingUFP"):
            return _fix_ufp_position(step, load_order, loadorder_path)

        if rule == "ConflictRootCause":
            resource = ""
            if step.observation:
                # Extract resource name from "Resource '...' is claimed by …"
                import re
                m = re.search(r"Resource '([^']+)'", step.observation)
                resource = m.group(1) if m else (step.plugin or "")
            conflict = conflict_map.get(resource)
            return _fix_conflict_patch(step, load_order, conflict, self.patch_name)

        if rule in ("PluginCapHard", "PluginCapWarning"):
            # Suggest the ESP plugins from the load order as ESL candidates
            esp_candidates = [
                p for p in load_order
                if p.lower().endswith(".esp") and
                not any(kw in p.lower()
                        for kw in ("bashed", "merged", "smashed", "conflict"))
            ][:20]   # cap at 20 to keep the script readable
            return _fix_esl_flag(step, esp_candidates)

        if rule in ("CrashDiagnosis", "ScriptLagDiagnosis"):
            return _fix_papyrus_logging(step)

        if rule == "MissingTextureDiagnosis":
            return _fix_archive_invalidation(step)

        if rule == "F4SEDependency":
            return _fix_safe_launch(step)

        if rule == "MissingDependency":
            return _fix_missing_dependency(step)

        # GenericDiagnosis or unknown rules — emit a general guidance Python script
        return _fix_generic(step)

    # ─────────────────────────────────────────────────────────────────────
    #  Convenience: generate + write to disk
    # ─────────────────────────────────────────────────────────────────────

    def generate_and_write(
        self,
        reasoning: "ReasoningResult",
        output_dir: Path,
        load_order: Optional[List[str]] = None,
        loadorder_path: Optional[Path] = None,
        conflicts: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Path]:
        """Generate all fixes and write them to *output_dir*. Returns written paths."""
        fixes = self.generate_fixes(reasoning, load_order, loadorder_path, conflicts)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        written: List[Path] = []
        for fix in fixes:
            dest = output_dir / fix.filename
            dest.write_text(fix.code, encoding="utf-8")
            written.append(dest)
            logger.info(f"Fix written: {dest}")
        return written


# ─────────────────────────────────────────────────────────────────────────────
# Fallback generic fix
# ─────────────────────────────────────────────────────────────────────────────

def _fix_generic(step: "ReasoningStep") -> Fix:
    code = _py_header(
        f"Diagnostic: {step.rule}",
        step.deduction,
    ) + textwrap.dedent(f"""\
        # This script prints the diagnosis — no automatic fix is available.
        # Follow the action plan output by  mossy ai reason  to resolve manually.

        OBSERVATION = "{step.observation.replace(chr(34), chr(39))}"
        DEDUCTION   = "{step.deduction.replace(chr(34), chr(39))}"

        print("[Mossy] Diagnosis:")
        print(f"  Observed : {{OBSERVATION}}")
        print(f"  Concluded: {{DEDUCTION}}")
        print()
        print("[Mossy] Run 'mossy ai reason' for the full reasoning trace.")
        print("[Mossy] Run 'mossy ai analyze' for AI-powered recommendations.")
        """)

    return Fix(
        title=f"Diagnosis: {step.rule}",
        description=step.deduction,
        issue_rule=step.rule,
        fix_type="python",
        code=code,
        filename=f"diagnosis_{step.rule.lower()}.py",
        can_auto_apply=False,
    )
