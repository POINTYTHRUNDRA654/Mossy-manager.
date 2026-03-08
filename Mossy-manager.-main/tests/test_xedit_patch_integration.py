"""Tests for xEdit patch integration"""

import pytest
from pathlib import Path
import tempfile
import json

from mossy_manager.utils.xedit_integration import XEditIntegration
from mossy_manager.core.patcher import Patcher, Patch


class TestXEditPatchIntegration:
    """Test xEdit integration for patches"""
    
    def test_export_patch_for_xedit(self):
        """Test exporting patch to xEdit format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            xedit = XEditIntegration()
            
            patch_data = {
                'name': 'TestPatch',
                'description': 'Test patch for xEdit',
                'created_at': '2026-02-09T00:00:00',
                'operations': [
                    {
                        'type': 'merge',
                        'file': 'Data/config.ini',
                        'content': 'test=1'
                    },
                    {
                        'type': 'replace',
                        'file': 'Data/settings.txt',
                        'content': 'new content'
                    }
                ],
                'target_mods': ['ModA', 'ModB']
            }
            
            output_path = Path(tmpdir) / "patch.json"
            xedit.export_patch_for_xedit(patch_data, output_path)
            
            assert output_path.exists()
            
            # Verify content
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data['version'] == '1.0'
            assert data['patch']['name'] == 'TestPatch'
            assert len(data['patch']['operations']) == 2
    
    def test_generate_patch_script(self):
        """Test generating xEdit script for patch"""
        with tempfile.TemporaryDirectory() as tmpdir:
            xedit = XEditIntegration()
            
            patch_data = {
                'name': 'MyPatch',
                'description': 'Test patch',
                'operations': [
                    {'type': 'add', 'file': 'test.txt', 'content': 'data'}
                ],
                'target_mods': []
            }
            
            script_path = xedit.generate_patch_script(
                patch_data,
                Path(tmpdir),
                target_plugin='MyPatch.esp'
            )
            
            assert script_path.exists()
            assert script_path.suffix == '.pas'
            
            # Verify script content
            with open(script_path, 'r') as f:
                content = f.read()
            
            assert 'unit MyPatch_Apply' in content
            assert 'MyPatch.esp' in content
            assert 'Initialize' in content
    
    def test_build_patch_script(self):
        """Test building patch script content"""
        xedit = XEditIntegration()
        
        patch_data = {
            'name': 'TestPatch',
            'description': 'A test patch',
            'operations': [
                {'type': 'merge', 'file': 'config.ini'},
                {'type': 'replace', 'file': 'data.txt'}
            ],
            'target_mods': ['ModA']
        }
        
        script = xedit._build_patch_script(patch_data, 'TestPatch', 'TestPatch.esp')
        
        assert 'unit TestPatch_Apply' in script
        assert 'TestPatch.esp' in script
        assert 'merge' in script
        assert 'replace' in script
    
    def test_create_patch_with_xedit(self):
        """Test full patch creation workflow with xEdit"""
        with tempfile.TemporaryDirectory() as tmpdir:
            xedit = XEditIntegration()
            
            patch_data = {
                'name': 'ComplexPatch',
                'description': 'Complex test patch',
                'operations': [
                    {'type': 'add', 'file': 'new.txt', 'content': 'new'},
                    {'type': 'merge', 'file': 'config.ini', 'content': 'setting=1'}
                ],
                'target_mods': ['ModA', 'ModB']
            }
            
            result = xedit.create_patch_with_xedit(
                patch_data,
                Path(tmpdir),
                target_plugin='ComplexPatch.esp'
            )
            
            assert result['success'] is True
            assert result['patch_exported'] is True
            assert result['script_generated'] is True
            assert result['export_path'] is not None
            assert result['script_path'] is not None
            
            # Verify files exist
            assert Path(result['export_path']).exists()
            assert Path(result['script_path']).exists()
    
    def test_patcher_export_for_xedit(self):
        """Test Patcher class xEdit export"""
        patcher = Patcher()
        patch = patcher.create_patch('TestPatch', 'Test description')
        patch.add_operation('merge', file='test.ini', content='data')
        patch.target_mods = ['ModA']
        
        exported = patcher.export_for_xedit(patch)
        
        assert exported['name'] == 'TestPatch'
        assert exported['description'] == 'Test description'
        assert len(exported['operations']) == 1
        assert exported['target_mods'] == ['ModA']
    
    def test_patch_script_with_special_characters(self):
        """Test patch script with special characters in description"""
        xedit = XEditIntegration()
        
        patch_data = {
            'name': "Patch's Test",
            'description': "A patch with 'quotes' in it",
            'operations': [],
            'target_mods': []
        }
        
        script = xedit._build_patch_script(patch_data, 'Patch_s_Test', 'Test.esp')
        
        # Should have properly escaped quotes in the AddMessage line
        assert "AddMessage('Description: A patch with ''quotes'' in it');" in script
    
    def test_patch_export_with_empty_operations(self):
        """Test exporting patch with no operations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            xedit = XEditIntegration()
            
            patch_data = {
                'name': 'EmptyPatch',
                'description': 'Empty test patch',
                'operations': [],
                'target_mods': []
            }
            
            output_path = Path(tmpdir) / "empty_patch.json"
            xedit.export_patch_for_xedit(patch_data, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data['patch']['name'] == 'EmptyPatch'
            assert len(data['patch']['operations']) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
