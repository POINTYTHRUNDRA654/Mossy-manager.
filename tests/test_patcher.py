"""Tests for Patcher"""

import pytest
from pathlib import Path
import tempfile
import os
import json

from mossy_manager.core.patcher import Patcher, Patch


class TestPatch:
    """Test Patch class"""
    
    def test_patch_creation(self):
        """Test creating a patch"""
        patch = Patch("TestPatch", "Test description")
        
        assert patch.name == "TestPatch"
        assert patch.description == "Test description"
        assert len(patch.operations) == 0
        assert len(patch.target_mods) == 0
    
    def test_add_operation(self):
        """Test adding operations to a patch"""
        patch = Patch("TestPatch")
        
        patch.add_operation("replace", file="test.txt", content="new content")
        
        assert len(patch.operations) == 1
        assert patch.operations[0]['type'] == "replace"
        assert patch.operations[0]['file'] == "test.txt"
    
    def test_to_dict(self):
        """Test converting patch to dictionary"""
        patch = Patch("TestPatch", "Description")
        patch.add_operation("add", file="new.txt", content="content")
        
        patch_dict = patch.to_dict()
        
        assert patch_dict['name'] == "TestPatch"
        assert patch_dict['description'] == "Description"
        assert len(patch_dict['operations']) == 1
    
    def test_from_dict(self):
        """Test creating patch from dictionary"""
        data = {
            'name': 'TestPatch',
            'description': 'Test',
            'operations': [
                {'type': 'add', 'file': 'test.txt', 'content': 'data'}
            ],
            'target_mods': ['ModA']
        }
        
        patch = Patch.from_dict(data)
        
        assert patch.name == 'TestPatch'
        assert len(patch.operations) == 1
        assert len(patch.target_mods) == 1


class TestPatcher:
    """Test Patcher class"""
    
    def test_patcher_creation(self):
        """Test creating a patcher"""
        with tempfile.TemporaryDirectory() as tmpdir:
            patcher = Patcher(Path(tmpdir))
            assert patcher.patches_dir == Path(tmpdir)
            assert len(patcher.patches) == 0
    
    def test_create_patch(self):
        """Test creating a new patch"""
        patcher = Patcher()
        
        patch = patcher.create_patch("TestPatch", "Description")
        
        assert patch.name == "TestPatch"
        assert patch.description == "Description"
        assert "TestPatch" in patcher.patches
    
    def test_save_and_load_patch(self):
        """Test saving and loading a patch"""
        with tempfile.TemporaryDirectory() as tmpdir:
            patcher = Patcher(Path(tmpdir))
            
            # Create and save a patch
            patch = patcher.create_patch("TestPatch", "Test Description")
            patch.add_operation("replace", file="test.txt", content="new content")
            
            saved_path = patcher.save_patch(patch)
            
            assert saved_path.exists()
            assert saved_path.name == "TestPatch.json"
            
            # Load the patch
            patcher2 = Patcher(Path(tmpdir))
            loaded_patch = patcher2.load_patch(saved_path)
            
            assert loaded_patch.name == "TestPatch"
            assert loaded_patch.description == "Test Description"
            assert len(loaded_patch.operations) == 1
    
    def test_list_patches(self):
        """Test listing patches"""
        with tempfile.TemporaryDirectory() as tmpdir:
            patcher = Patcher(Path(tmpdir))
            
            # Create multiple patches
            patch1 = patcher.create_patch("Patch1")
            patch2 = patcher.create_patch("Patch2")
            
            patcher.save_patch(patch1)
            patcher.save_patch(patch2)
            
            patches = patcher.list_patches()
            
            assert len(patches) >= 2
            assert "Patch1" in patches
            assert "Patch2" in patches
    
    def test_apply_patch_replace(self):
        """Test applying a replace operation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_path = Path(tmpdir) / "mod"
            mod_path.mkdir()
            
            # Create a file to replace
            test_file = mod_path / "test.txt"
            test_file.write_text("old content")
            
            # Create and apply patch
            patcher = Patcher()
            patch = patcher.create_patch("TestPatch")
            patch.add_operation("replace", file="test.txt", content="new content")
            
            result = patcher.apply_patch(patch, mod_path)
            
            assert result['success'] is True
            assert result['applied_operations'] == 1
            assert test_file.read_text() == "new content"
    
    def test_apply_patch_add(self):
        """Test applying an add operation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_path = Path(tmpdir) / "mod"
            mod_path.mkdir()
            
            patcher = Patcher()
            patch = patcher.create_patch("TestPatch")
            patch.add_operation("add", file="new.txt", content="new file content")
            
            result = patcher.apply_patch(patch, mod_path)
            
            assert result['success'] is True
            new_file = mod_path / "new.txt"
            assert new_file.exists()
            assert new_file.read_text() == "new file content"
    
    def test_apply_patch_delete(self):
        """Test applying a delete operation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_path = Path(tmpdir) / "mod"
            mod_path.mkdir()
            
            # Create a file to delete
            test_file = mod_path / "delete_me.txt"
            test_file.write_text("content")
            
            patcher = Patcher()
            patch = patcher.create_patch("TestPatch")
            patch.add_operation("delete", file="delete_me.txt")
            
            result = patcher.apply_patch(patch, mod_path)
            
            assert result['success'] is True
            assert not test_file.exists()
    
    def test_apply_patch_merge(self):
        """Test applying a merge operation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_path = Path(tmpdir) / "mod"
            mod_path.mkdir()
            
            # Create existing file
            test_file = mod_path / "merge.txt"
            test_file.write_text("existing content")
            
            patcher = Patcher()
            patch = patcher.create_patch("TestPatch")
            patch.add_operation("merge", file="merge.txt", content="added content")
            
            result = patcher.apply_patch(patch, mod_path)
            
            assert result['success'] is True
            content = test_file.read_text()
            assert "existing content" in content
            assert "added content" in content
    
    def test_apply_patch_dry_run(self):
        """Test applying patch with dry run"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_path = Path(tmpdir) / "mod"
            mod_path.mkdir()
            
            test_file = mod_path / "test.txt"
            test_file.write_text("original")
            
            patcher = Patcher()
            patch = patcher.create_patch("TestPatch")
            patch.add_operation("replace", file="test.txt", content="modified")
            
            # Apply with dry run
            result = patcher.apply_patch(patch, mod_path, dry_run=True)
            
            assert result['success'] is True
            # File should not be modified
            assert test_file.read_text() == "original"
    
    def test_create_compatibility_patch(self):
        """Test creating a compatibility patch"""
        patcher = Patcher()
        
        conflicts = ["texture1.dds", "texture2.dds", "script.pex"]
        
        patch = patcher.create_compatibility_patch(
            "Compat_ModA_ModB",
            "ModA",
            "ModB",
            conflicts
        )
        
        assert patch.name == "Compat_ModA_ModB"
        assert "ModA" in patch.target_mods
        assert "ModB" in patch.target_mods
        assert len(patch.operations) == len(conflicts)
    
    def test_validate_patch(self):
        """Test validating a patch"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_path = Path(tmpdir) / "mod"
            mod_path.mkdir()
            
            # Create existing file
            (mod_path / "existing.txt").touch()
            
            patcher = Patcher()
            patch = patcher.create_patch("TestPatch")
            patch.add_operation("replace", file="existing.txt", content="new")
            patch.add_operation("replace", file="missing.txt", content="new")
            
            validation = patcher.validate_patch(patch, mod_path)
            
            assert 'valid' in validation
            assert 'warnings' in validation
            assert 'errors' in validation
            
            # Should have warning about missing file
            assert len(validation['warnings']) > 0
    
    def test_get_statistics(self):
        """Test getting statistics"""
        with tempfile.TemporaryDirectory() as tmpdir:
            patcher = Patcher(Path(tmpdir))
            
            patch1 = patcher.create_patch("Patch1")
            patch1.add_operation("add", file="test.txt", content="data")
            patch1.add_operation("replace", file="test2.txt", content="data")
            
            patch2 = patcher.create_patch("Patch2")
            patch2.add_operation("delete", file="test.txt")
            
            patcher.save_patch(patch1)
            patcher.save_patch(patch2)
            
            stats = patcher.get_statistics()
            
            assert stats['total_patches'] == 2
            assert stats['total_operations'] == 3
            assert stats['saved_patches'] == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
