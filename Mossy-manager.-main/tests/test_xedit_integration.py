"""Tests for xEdit Integration"""

import pytest
from pathlib import Path
import tempfile
import json

from mossy_manager.utils.xedit_integration import XEditIntegration


class TestXEditIntegration:
    """Test XEditIntegration class"""
    
    def test_xedit_creation(self):
        """Test creating xEdit integration"""
        xedit = XEditIntegration()
        assert xedit.xedit_path is None
        assert xedit.game_data_path is None
        assert len(xedit.supported_games) > 0
    
    def test_supported_games(self):
        """Test supported games list"""
        xedit = XEditIntegration()
        assert 'skyrimse' in xedit.supported_games
        assert 'fallout4' in xedit.supported_games
        assert xedit.supported_games['skyrimse'] == 'SSEEdit.exe'
        assert xedit.supported_games['fallout4'] == 'FO4Edit.exe'

    def test_detect_xedit_default_game_is_fallout4(self):
        """detect_xedit should default to fallout4, not skyrimse"""
        import inspect
        sig = inspect.signature(XEditIntegration.detect_xedit)
        assert sig.parameters['game'].default == 'fallout4'
    
    def test_export_conflicts(self):
        """Test exporting conflicts for xEdit"""
        with tempfile.TemporaryDirectory() as tmpdir:
            xedit = XEditIntegration()
            
            conflicts = [
                {
                    'type': 'plugin_conflict',
                    'resource': 'TestMod.esp',
                    'severity': 'critical',
                    'mods': ['ModA', 'ModB']
                },
                {
                    'type': 'resource_conflict',
                    'resource': 'textures/test.dds',
                    'severity': 'medium',
                    'mods': ['ModC', 'ModD']
                }
            ]
            
            output_path = Path(tmpdir) / "conflicts.json"
            xedit.export_conflicts_for_xedit(conflicts, output_path)
            
            assert output_path.exists()
            
            # Verify content
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert 'version' in data
            assert 'conflicts' in data
            assert len(data['conflicts']) == 2
    
    def test_extract_plugins_from_conflict(self):
        """Test extracting plugins from conflict"""
        xedit = XEditIntegration()
        
        # Conflict with plugin
        conflict1 = {
            'resource': 'SomeMod.esp',
            'type': 'plugin_conflict'
        }
        plugins1 = xedit._extract_plugins_from_conflict(conflict1)
        assert 'SomeMod.esp' in plugins1
        
        # Conflict without plugin
        conflict2 = {
            'resource': 'textures/test.dds',
            'type': 'resource_conflict'
        }
        plugins2 = xedit._extract_plugins_from_conflict(conflict2)
        assert len(plugins2) == 0
    
    def test_generate_xedit_script(self):
        """Test generating xEdit script"""
        with tempfile.TemporaryDirectory() as tmpdir:
            xedit = XEditIntegration()
            
            conflicts = [
                {
                    'type': 'plugin_conflict',
                    'resource': 'ModA.esp',
                    'severity': 'critical',
                    'mods': ['ModA', 'ModB']
                }
            ]
            
            script_path = xedit.generate_xedit_script(
                conflicts,
                Path(tmpdir),
                "TestPatch"
            )
            
            assert script_path.exists()
            assert script_path.suffix == '.pas'
            
            # Verify script contains expected content
            with open(script_path, 'r') as f:
                content = f.read()
            
            assert 'unit TestPatch_Script' in content
            assert 'TestPatch.esp' in content
    
    def test_build_xedit_script(self):
        """Test building xEdit script content"""
        xedit = XEditIntegration()
        
        conflicts = [
            {
                'resource': 'Test.esp',
                'type': 'plugin_conflict'
            }
        ]
        
        script = xedit._build_xedit_script(conflicts, "MyPatch")
        
        assert 'unit MyPatch_Script' in script
        assert 'MyPatch.esp' in script
        assert 'Initialize' in script
        assert 'Process' in script
        assert 'Finalize' in script
    
    def test_create_conflict_resolution_patch(self):
        """Test high-level patch creation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            xedit = XEditIntegration()
            
            conflicts = [
                {
                    'type': 'plugin_conflict',
                    'resource': 'TestMod.esp',
                    'severity': 'critical',
                    'mods': ['ModA', 'ModB']
                }
            ]
            
            result = xedit.create_conflict_resolution_patch(
                conflicts,
                "TestPatch",
                Path(tmpdir)
            )
            
            assert result['success'] is True
            assert result['conflicts_exported'] is True
            assert result['script_generated'] is True
            assert result['export_path'] is not None
            assert result['script_path'] is not None
            
            # Verify files exist
            assert Path(result['export_path']).exists()
            assert Path(result['script_path']).exists()
    
    def test_configuration_help(self):
        """Test getting configuration help"""
        xedit = XEditIntegration()
        help_text = xedit.get_configuration_help()
        
        assert 'xEdit Configuration Guide' in help_text
        assert 'SSEEdit' in help_text
        assert 'Download from' in help_text


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
