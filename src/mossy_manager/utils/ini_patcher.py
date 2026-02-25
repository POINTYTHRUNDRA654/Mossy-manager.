"""
INIPatcher — read, write and apply presets to Fallout 4 INI files.

Fallout 4 uses three INI files that are always located inside the user's
``Documents\\My Games\\Fallout4`` folder:

  Fallout4.ini       — primary settings (managed by the game)
  Fallout4Prefs.ini  — launcher preferences
  Fallout4Custom.ini — user overrides (never touched by the game or launcher)

The recommended practice for mods is to put **all** custom settings in
``Fallout4Custom.ini`` so that game/launcher updates cannot overwrite them.
That is the file ``write_value()`` and ``apply_preset()`` target by default.

API
---
::

    patcher = INIPatcher(game_docs_path=Path(r"C:/Users/Me/Documents/My Games/Fallout4"))

    # Read current values
    val = patcher.read_value("Papyrus", "bEnableLogging")   # "1" or None

    # Write a single value safely (writes to Fallout4Custom.ini by default)
    patcher.write_value("Papyrus", "bEnableLogging", "1")

    # Apply a named preset (papyrus_logging, archive_invalidation,
    #                       performance_high, performance_low, f4se_compat)
    patcher.apply_preset("papyrus_logging")

    # Make a timestamped backup before modifying
    backup_path = patcher.backup_ini("Fallout4Custom.ini")
"""

from __future__ import annotations

import configparser
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Known presets — identical to what ScriptWriter.ini_tweak() generates as text,
# but here as structured (section, key, value) tuples that can be applied
# programmatically.
# ─────────────────────────────────────────────────────────────────────────────

_PRESETS: Dict[str, List[Tuple[str, str, str]]] = {
    "papyrus_logging": [
        ("Papyrus", "bEnableLogging",         "1"),
        ("Papyrus", "bEnableTrace",            "1"),
        ("Papyrus", "bLoadDebugInformation",   "1"),
        ("Papyrus", "iMaxAllocatedMemoryBytes","786432"),
    ],
    "papyrus_logging_off": [
        ("Papyrus", "bEnableLogging",         "0"),
        ("Papyrus", "bEnableTrace",            "0"),
        ("Papyrus", "bLoadDebugInformation",   "0"),
    ],
    "archive_invalidation": [
        ("Archive", "bInvalidateOlderFiles",   "1"),
        ("Archive", "sResourceDataDirsFinal",  ""),
    ],
    "archive_invalidation_off": [
        ("Archive", "bInvalidateOlderFiles",   "0"),
    ],
    "performance_high": [
        ("General",  "uExterior Cell Buffer",  "64"),
        ("General",  "iPreloadSizeLimit",      "26214400"),
        ("Display",  "fShadowDistance",        "3000"),
        ("Display",  "iShadowMapResolution",   "2048"),
        ("Display",  "bFull Screen",           "1"),
    ],
    "performance_low": [
        ("General",  "uExterior Cell Buffer",  "36"),
        ("General",  "iPreloadSizeLimit",      "13107200"),
        ("Display",  "fShadowDistance",        "1500"),
        ("Display",  "iShadowMapResolution",   "512"),
    ],
    "f4se_compat": [
        ("Launcher",  "bEnableFileSelection",  "1"),
        ("Archive",   "bInvalidateOlderFiles", "1"),
        ("Archive",   "sResourceDataDirsFinal",""),
    ],
}

PRESET_NAMES = sorted(_PRESETS)


# ─────────────────────────────────────────────────────────────────────────────
# INIPatcher
# ─────────────────────────────────────────────────────────────────────────────

class INIPatcher:
    """
    Safe reader/writer for Fallout 4 INI configuration files.

    Parameters
    ----------
    game_docs_path : Path, optional
        Path to ``Documents/My Games/Fallout4``.  When *None* the patcher
        resolves it automatically from ``~``.
    """

    _FO4_INI_NAMES = ("Fallout4.ini", "Fallout4Prefs.ini", "Fallout4Custom.ini")

    def __init__(self, game_docs_path: Optional[Path] = None) -> None:
        if game_docs_path is not None:
            self.game_docs_path = Path(game_docs_path)
        else:
            self.game_docs_path = self._default_docs_path()

    # ── Path helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _default_docs_path() -> Path:
        """Return the standard Fallout 4 documents path (Windows-centric)."""
        return Path.home() / "Documents" / "My Games" / "Fallout4"

    def ini_path(self, filename: str = "Fallout4Custom.ini") -> Path:
        """Absolute path to *filename* inside the game docs folder."""
        return self.game_docs_path / filename

    # ── ConfigParser helpers ──────────────────────────────────────────────

    @staticmethod
    def _make_parser() -> configparser.RawConfigParser:
        """
        A RawConfigParser that:
        - preserves key case (Bethesda INIs are case-sensitive)
        - allows values with no ``=`` (bare keys)
        - does NOT interpolate ``%`` or ``$`` characters
        """
        parser = configparser.RawConfigParser()
        parser.optionxform = str   # preserve case
        return parser

    def _read_ini(self, filepath: Path) -> configparser.RawConfigParser:
        """Read an INI file, returning an empty parser if the file is absent."""
        parser = self._make_parser()
        if filepath.exists():
            try:
                parser.read(filepath, encoding="utf-8")
            except configparser.Error:
                # Bethesda INIs sometimes have bare section headers with no keys
                logger.warning(f"Partial parse of {filepath} — continuing")
        return parser

    def _write_ini(self, parser: configparser.RawConfigParser,
                   filepath: Path) -> None:
        """Write *parser* to *filepath*, creating parent dirs as needed."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as fh:
            parser.write(fh)

    # ── Public API ────────────────────────────────────────────────────────

    def read_value(
        self,
        section: str,
        key: str,
        filename: str = "Fallout4.ini",
    ) -> Optional[str]:
        """
        Read a single INI value.

        Searches *filename* first, then ``Fallout4Custom.ini`` if not found.

        Parameters
        ----------
        section : str
            INI section name (e.g. ``"Papyrus"``).
        key : str
            Key name (e.g. ``"bEnableLogging"``).
        filename : str
            Which INI file to read (default ``"Fallout4.ini"``).

        Returns
        -------
        str or None
            The raw string value, or *None* when not present.
        """
        parser = self._read_ini(self.ini_path(filename))
        if parser.has_option(section, key):
            return parser.get(section, key)
        # Fall back to Custom.ini
        if filename != "Fallout4Custom.ini":
            custom = self._read_ini(self.ini_path("Fallout4Custom.ini"))
            if custom.has_option(section, key):
                return custom.get(section, key)
        return None

    def read_section(
        self,
        section: str,
        filename: str = "Fallout4.ini",
    ) -> Dict[str, str]:
        """
        Return all key=value pairs in *section* from *filename*.

        Returns an empty dict when the section does not exist.
        """
        parser = self._read_ini(self.ini_path(filename))
        if parser.has_section(section):
            return dict(parser.items(section))
        return {}

    def write_value(
        self,
        section: str,
        key: str,
        value: str,
        filename: str = "Fallout4Custom.ini",
    ) -> Path:
        """
        Write (or overwrite) a single key in *filename*.

        Writes to ``Fallout4Custom.ini`` by default so that game / launcher
        updates cannot clobber the setting.

        Parameters
        ----------
        section, key, value : str
            INI section, key, and value to write.
        filename : str
            Target INI file (default ``"Fallout4Custom.ini"``).

        Returns
        -------
        Path
            Path to the file that was written.
        """
        filepath = self.ini_path(filename)
        parser = self._read_ini(filepath)

        if not parser.has_section(section):
            parser.add_section(section)
        parser.set(section, key, value)

        self._write_ini(parser, filepath)
        logger.info(f"INI write: [{section}] {key}={value} → {filepath}")
        return filepath

    def write_values(
        self,
        settings: List[Tuple[str, str, str]],
        filename: str = "Fallout4Custom.ini",
    ) -> Path:
        """
        Write multiple ``(section, key, value)`` triples in one pass.

        Parameters
        ----------
        settings : list of (section, key, value) tuples
        filename : str

        Returns
        -------
        Path
            Path to the file that was written.
        """
        filepath = self.ini_path(filename)
        parser = self._read_ini(filepath)

        for section, key, value in settings:
            if not parser.has_section(section):
                parser.add_section(section)
            parser.set(section, key, value)

        self._write_ini(parser, filepath)
        logger.info(f"INI batch write: {len(settings)} values → {filepath}")
        return filepath

    def apply_preset(
        self,
        preset_name: str,
        filename: str = "Fallout4Custom.ini",
        backup: bool = True,
    ) -> Tuple[Path, Optional[Path]]:
        """
        Apply a named preset to *filename*.

        Available presets: ``papyrus_logging``, ``papyrus_logging_off``,
        ``archive_invalidation``, ``archive_invalidation_off``,
        ``performance_high``, ``performance_low``, ``f4se_compat``.

        Parameters
        ----------
        preset_name : str
            Name of the preset to apply.
        filename : str
            Target INI file (default ``"Fallout4Custom.ini"``).
        backup : bool
            When *True* (default) a timestamped backup is made before writing.

        Returns
        -------
        (Path, Path or None)
            ``(written_file, backup_file)``.  *backup_file* is *None* when
            *backup=False* or when the target file did not yet exist.

        Raises
        ------
        ValueError
            When *preset_name* is not a known preset.
        """
        if preset_name not in _PRESETS:
            raise ValueError(
                f"Unknown INI preset '{preset_name}'. "
                f"Available: {sorted(_PRESETS)}"
            )

        filepath = self.ini_path(filename)
        backup_path: Optional[Path] = None
        if backup and filepath.exists():
            backup_path = self.backup_ini(filename)

        written = self.write_values(_PRESETS[preset_name], filename)
        logger.info(f"Applied preset '{preset_name}' to {written}")
        return written, backup_path

    def backup_ini(self, filename: str = "Fallout4Custom.ini") -> Optional[Path]:
        """
        Make a timestamped copy of *filename* in the same directory.

        Returns the backup path, or *None* when the source file does not exist.
        """
        source = self.ini_path(filename)
        if not source.exists():
            return None
        stem = source.stem
        suffix = source.suffix
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        dest = source.parent / f"{stem}_backup_{ts}{suffix}"
        shutil.copy2(source, dest)
        logger.info(f"INI backup: {source} → {dest}")
        return dest

    def get_all_values(
        self, filename: str = "Fallout4Custom.ini"
    ) -> Dict[str, Dict[str, str]]:
        """
        Return the entire contents of *filename* as a nested dict.

        ``{ section: { key: value, … }, … }``
        """
        parser = self._read_ini(self.ini_path(filename))
        return {
            section: dict(parser.items(section))
            for section in parser.sections()
        }

    def diff(
        self,
        filename_a: str = "Fallout4.ini",
        filename_b: str = "Fallout4Custom.ini",
    ) -> Dict[str, Dict[str, Tuple[Optional[str], Optional[str]]]]:
        """
        Compare two INI files and return differing keys.

        Returns a dict ``{ section: { key: (value_a, value_b) } }``
        for every key where the values differ (including keys present in
        only one file).
        """
        pa = self._read_ini(self.ini_path(filename_a))
        pb = self._read_ini(self.ini_path(filename_b))

        all_sections: set = set(pa.sections()) | set(pb.sections())
        result: Dict[str, Dict[str, Tuple[Optional[str], Optional[str]]]] = {}

        for section in all_sections:
            a_keys = dict(pa.items(section)) if pa.has_section(section) else {}
            b_keys = dict(pb.items(section)) if pb.has_section(section) else {}
            all_keys = set(a_keys) | set(b_keys)
            diffs = {}
            for key in all_keys:
                va = a_keys.get(key)
                vb = b_keys.get(key)
                if va != vb:
                    diffs[key] = (va, vb)
            if diffs:
                result[section] = diffs

        return result

    def validate_preset_applied(
        self,
        preset_name: str,
        filename: str = "Fallout4Custom.ini",
    ) -> Tuple[bool, List[str]]:
        """
        Check whether a preset has been fully applied to *filename*.

        Returns ``(all_applied: bool, missing_or_wrong: List[str])``.
        """
        if preset_name not in _PRESETS:
            raise ValueError(f"Unknown preset: {preset_name}")

        parser = self._read_ini(self.ini_path(filename))
        problems: List[str] = []

        for section, key, expected in _PRESETS[preset_name]:
            if not parser.has_option(section, key):
                problems.append(f"[{section}] {key} not set (expected '{expected}')")
            else:
                actual = parser.get(section, key)
                if actual.strip() != expected.strip():
                    problems.append(
                        f"[{section}] {key}='{actual}' (expected '{expected}')"
                    )

        return (len(problems) == 0), problems
