"""
BackupManager — centralised profile backup / restore for Mossy Manager.

Replaces the scattered inline ``shutil.copytree`` calls in the CLI and
web-app with a single, well-tested helper that:

* Creates dated, labelled backups
* Lists existing backups with metadata (size, age, label)
* Restores a backup to the original profile location
* Prunes old backups so the disk doesn't fill up
"""

from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BackupEntry:
    """Metadata about a single backup directory."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._meta: Dict[str, Any] = self._load_meta()

    def _load_meta(self) -> Dict[str, Any]:
        meta_file = self.path / ".mossy_backup_meta.json"
        if meta_file.exists():
            try:
                return json.loads(meta_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        # Fall back to info inferred from directory name
        return {}

    @property
    def label(self) -> str:
        return self._meta.get("label", self.path.name)

    @property
    def created_at(self) -> str:
        return self._meta.get("created_at", "unknown")

    @property
    def source_profile(self) -> str:
        return self._meta.get("source_profile", "unknown")

    @property
    def size_bytes(self) -> int:
        """Total size of the backup directory in bytes."""
        try:
            return sum(f.stat().st_size for f in self.path.rglob("*") if f.is_file())
        except Exception:
            return 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": str(self.path),
            "label": self.label,
            "created_at": self.created_at,
            "source_profile": self.source_profile,
            "size_bytes": self.size_bytes,
        }

    def __repr__(self) -> str:
        return f"BackupEntry({self.label!r}, created={self.created_at})"


class BackupManager:
    """
    Manages timestamped backups of MO2 profile directories.

    Parameters
    ----------
    backups_root : Path
        Root directory under which all backups are stored.
        A sub-directory is created for each backup.
    """

    def __init__(self, backups_root: Path) -> None:
        self.backups_root = Path(backups_root)
        self.backups_root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    #  Create                                                              #
    # ------------------------------------------------------------------ #

    def create_backup(
        self,
        source_path: Path,
        label: str = "",
        profile_name: str = "",
    ) -> Path:
        """
        Copy *source_path* into a new dated backup directory.

        Parameters
        ----------
        source_path : Path
            Directory to back up (typically an MO2 profile folder).
        label : str
            Optional human-readable label (e.g. "before-auto-optimize").
        profile_name : str
            The MO2 profile name, stored in metadata for easy identification.

        Returns
        -------
        Path
            Path to the newly created backup directory.

        Raises
        ------
        FileNotFoundError
            If *source_path* does not exist.
        """
        source_path = Path(source_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Source path does not exist: {source_path}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        safe_label = label.replace(" ", "_") if label else ""
        dir_name = f"{source_path.name}_backup_{timestamp}"
        if safe_label:
            dir_name = f"{dir_name}_{safe_label}"

        dest = self.backups_root / dir_name
        shutil.copytree(source_path, dest)

        # Write metadata
        meta = {
            "label": label or dir_name,
            "created_at": datetime.now().isoformat(),
            "source_path": str(source_path),
            "source_profile": profile_name or source_path.name,
            "timestamp": timestamp,
        }
        (dest / ".mossy_backup_meta.json").write_text(
            json.dumps(meta, indent=2), encoding="utf-8"
        )

        logger.info(f"Backup created: {dest}")
        return dest

    # ------------------------------------------------------------------ #
    #  List                                                                #
    # ------------------------------------------------------------------ #

    def list_backups(self, profile_name: Optional[str] = None) -> List[BackupEntry]:
        """
        Return all backups, optionally filtered to a specific *profile_name*.

        Sorted newest-first.
        """
        entries = []
        for child in self.backups_root.iterdir():
            if child.is_dir():
                entry = BackupEntry(child)
                if profile_name and entry.source_profile != profile_name:
                    continue
                entries.append(entry)

        entries.sort(key=lambda e: e.created_at, reverse=True)
        return entries

    # ------------------------------------------------------------------ #
    #  Restore                                                             #
    # ------------------------------------------------------------------ #

    def restore_backup(
        self,
        backup_path: Path,
        target_path: Path,
        overwrite: bool = True,
    ) -> bool:
        """
        Restore a backup to *target_path*.

        Parameters
        ----------
        backup_path : Path
            The backup directory to restore from.
        target_path : Path
            Where to restore to (usually the original profile folder).
        overwrite : bool
            If *True* (default) and *target_path* exists, it is removed first.

        Returns
        -------
        bool
            ``True`` on success.
        """
        backup_path = Path(backup_path)
        target_path = Path(target_path)

        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")

        if target_path.exists():
            if overwrite:
                shutil.rmtree(target_path)
            else:
                raise FileExistsError(
                    f"Target already exists: {target_path}. "
                    "Pass overwrite=True to replace it."
                )

        # Copy everything except our meta file so the profile is clean
        shutil.copytree(
            backup_path,
            target_path,
            ignore=shutil.ignore_patterns(".mossy_backup_meta.json"),
        )
        logger.info(f"Restored {backup_path} → {target_path}")
        return True

    # ------------------------------------------------------------------ #
    #  Cleanup                                                             #
    # ------------------------------------------------------------------ #

    def cleanup_old_backups(
        self,
        keep: int = 5,
        profile_name: Optional[str] = None,
    ) -> int:
        """
        Delete old backups, keeping the *keep* most recent ones.

        Parameters
        ----------
        keep : int
            Number of most-recent backups to retain (default 5).
        profile_name : str, optional
            If given, only backups for this profile are considered.

        Returns
        -------
        int
            Number of backups deleted.
        """
        entries = self.list_backups(profile_name=profile_name)
        to_delete = entries[keep:]
        deleted = 0
        for entry in to_delete:
            try:
                shutil.rmtree(entry.path)
                deleted += 1
                logger.info(f"Deleted old backup: {entry.path}")
            except Exception as exc:
                logger.warning(f"Could not delete backup {entry.path}: {exc}")
        return deleted

    # ------------------------------------------------------------------ #
    #  Utility                                                             #
    # ------------------------------------------------------------------ #

    def total_size_bytes(self) -> int:
        """Return the combined size of all backups in bytes."""
        return sum(e.size_bytes for e in self.list_backups())
