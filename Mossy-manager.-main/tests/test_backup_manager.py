"""
Tests for the BackupManager utility.
"""

import json
import pytest
import tempfile
from pathlib import Path

from mossy_manager.utils.backup_manager import BackupManager, BackupEntry


@pytest.fixture
def tmpdir_pair(tmp_path):
    """Return (source_profile_dir, backups_root) as Paths."""
    source = tmp_path / "profiles" / "Default"
    source.mkdir(parents=True)
    (source / "modlist.txt").write_text("+MyMod\n")
    (source / "plugins.txt").write_text("*Fallout4.esm\n")
    (source / "loadorder.txt").write_text("Fallout4.esm\n")
    backups_root = tmp_path / "backups"
    return source, backups_root


class TestBackupManagerCreate:
    def test_create_returns_path(self, tmpdir_pair):
        source, backups_root = tmpdir_pair
        mgr = BackupManager(backups_root)
        dest = mgr.create_backup(source)
        assert dest.exists()
        assert dest.is_dir()

    def test_create_copies_files(self, tmpdir_pair):
        source, backups_root = tmpdir_pair
        mgr = BackupManager(backups_root)
        dest = mgr.create_backup(source)
        assert (dest / "modlist.txt").exists()
        assert (dest / "plugins.txt").exists()

    def test_create_writes_meta(self, tmpdir_pair):
        source, backups_root = tmpdir_pair
        mgr = BackupManager(backups_root)
        dest = mgr.create_backup(source, label="test-label", profile_name="Default")
        meta_file = dest / ".mossy_backup_meta.json"
        assert meta_file.exists()
        meta = json.loads(meta_file.read_text())
        assert meta["label"] == "test-label"
        assert meta["source_profile"] == "Default"

    def test_create_nonexistent_source_raises(self, tmp_path):
        mgr = BackupManager(tmp_path / "backups")
        with pytest.raises(FileNotFoundError):
            mgr.create_backup(tmp_path / "nonexistent")

    def test_create_multiple_backups(self, tmpdir_pair):
        source, backups_root = tmpdir_pair
        mgr = BackupManager(backups_root)
        mgr.create_backup(source, label="first")
        mgr.create_backup(source, label="second")
        assert len(list(backups_root.iterdir())) == 2


class TestBackupManagerList:
    def test_list_returns_entries(self, tmpdir_pair):
        source, backups_root = tmpdir_pair
        mgr = BackupManager(backups_root)
        mgr.create_backup(source, profile_name="Default")
        entries = mgr.list_backups()
        assert len(entries) == 1
        assert isinstance(entries[0], BackupEntry)

    def test_list_empty_when_no_backups(self, tmp_path):
        mgr = BackupManager(tmp_path / "backups")
        assert mgr.list_backups() == []

    def test_list_filters_by_profile(self, tmpdir_pair):
        source, backups_root = tmpdir_pair
        mgr = BackupManager(backups_root)
        mgr.create_backup(source, profile_name="Default")
        mgr.create_backup(source, profile_name="Hardcore")
        default_only = mgr.list_backups(profile_name="Default")
        assert all(e.source_profile == "Default" for e in default_only)

    def test_list_sorted_newest_first(self, tmpdir_pair):
        source, backups_root = tmpdir_pair
        mgr = BackupManager(backups_root)
        mgr.create_backup(source, label="a")
        import time; time.sleep(0.02)
        mgr.create_backup(source, label="b")
        entries = mgr.list_backups()
        assert entries[0].label == "b"


class TestBackupManagerRestore:
    def test_restore_copies_files(self, tmpdir_pair, tmp_path):
        source, backups_root = tmpdir_pair
        mgr = BackupManager(backups_root)
        dest_backup = mgr.create_backup(source)
        target = tmp_path / "restored"
        mgr.restore_backup(dest_backup, target)
        assert (target / "modlist.txt").exists()
        assert (target / "plugins.txt").exists()

    def test_restore_excludes_meta_file(self, tmpdir_pair, tmp_path):
        source, backups_root = tmpdir_pair
        mgr = BackupManager(backups_root)
        dest_backup = mgr.create_backup(source)
        target = tmp_path / "restored"
        mgr.restore_backup(dest_backup, target)
        assert not (target / ".mossy_backup_meta.json").exists()

    def test_restore_nonexistent_backup_raises(self, tmp_path):
        mgr = BackupManager(tmp_path / "backups")
        with pytest.raises(FileNotFoundError):
            mgr.restore_backup(tmp_path / "nonexistent", tmp_path / "target")

    def test_restore_overwrite_false_raises_when_exists(self, tmpdir_pair, tmp_path):
        source, backups_root = tmpdir_pair
        mgr = BackupManager(backups_root)
        backup = mgr.create_backup(source)
        target = tmp_path / "target"
        target.mkdir()
        with pytest.raises(FileExistsError):
            mgr.restore_backup(backup, target, overwrite=False)

    def test_restore_returns_true(self, tmpdir_pair, tmp_path):
        source, backups_root = tmpdir_pair
        mgr = BackupManager(backups_root)
        backup = mgr.create_backup(source)
        result = mgr.restore_backup(backup, tmp_path / "out")
        assert result is True


class TestBackupManagerCleanup:
    def test_cleanup_deletes_old_backups(self, tmpdir_pair):
        source, backups_root = tmpdir_pair
        mgr = BackupManager(backups_root)
        import time
        for i in range(5):
            mgr.create_backup(source, label=f"b{i}")
            time.sleep(0.01)
        deleted = mgr.cleanup_old_backups(keep=2)
        assert deleted == 3
        assert len(mgr.list_backups()) == 2

    def test_cleanup_keeps_all_when_few_backups(self, tmpdir_pair):
        source, backups_root = tmpdir_pair
        mgr = BackupManager(backups_root)
        mgr.create_backup(source)
        deleted = mgr.cleanup_old_backups(keep=5)
        assert deleted == 0

    def test_total_size_bytes(self, tmpdir_pair):
        source, backups_root = tmpdir_pair
        mgr = BackupManager(backups_root)
        mgr.create_backup(source)
        size = mgr.total_size_bytes()
        assert size > 0


class TestBackupEntry:
    def test_entry_size_bytes(self, tmpdir_pair):
        source, backups_root = tmpdir_pair
        mgr = BackupManager(backups_root)
        backup = mgr.create_backup(source)
        entry = BackupEntry(backup)
        assert entry.size_bytes > 0

    def test_entry_to_dict(self, tmpdir_pair):
        source, backups_root = tmpdir_pair
        mgr = BackupManager(backups_root)
        backup = mgr.create_backup(source, label="test", profile_name="MyProfile")
        entry = BackupEntry(backup)
        d = entry.to_dict()
        assert "path" in d
        assert "label" in d
        assert "created_at" in d
        assert "size_bytes" in d


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
