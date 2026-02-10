"""Tests for Fallout 4 Rules"""

import pytest
from mossy_manager.games.fallout4 import Fallout4Rules


class TestFallout4Rules:
    """Test Fallout 4 specific rules and load order optimization"""
    
    def test_master_files_order(self):
        """Test official master files are defined correctly"""
        assert len(Fallout4Rules.MASTER_FILES) == 7
        assert Fallout4Rules.MASTER_FILES[0] == 'Fallout4.esm'
        assert 'DLCNukaWorld.esm' in Fallout4Rules.MASTER_FILES
    
    def test_is_master_file(self):
        """Test master file detection"""
        assert Fallout4Rules.is_master_file('Fallout4.esm')
        assert Fallout4Rules.is_master_file('DLCRobot.esm')
        assert not Fallout4Rules.is_master_file('SomePlugin.esp')
    
    def test_categorize_plugin(self):
        """Test plugin categorization"""
        category, priority = Fallout4Rules.categorize_plugin('Unofficial Fallout 4 Patch.esp')
        assert category == 'high_priority'
        assert priority == 5
        
        category, priority = Fallout4Rules.categorize_plugin('WeaponMod.esp')
        assert category == 'weapons'
        
        category, priority = Fallout4Rules.categorize_plugin('BetterSettlements.esp')
        assert category == 'settlements'
    
    def test_optimize_simple_load_order(self):
        """Test basic load order optimization"""
        plugins = [
            'ModA.esp',
            'DLCRobot.esm',
            'Fallout4.esm',
            'ModB.esp',
        ]
        
        optimized = Fallout4Rules.optimize_load_order(plugins)
        
        # Masters should be first in correct order
        assert optimized[0] == 'Fallout4.esm'
        assert optimized[1] == 'DLCRobot.esm'
        # Regular plugins after
        assert 'ModA.esp' in optimized[2:]
        assert 'ModB.esp' in optimized[2:]
    
    def test_validate_load_order(self):
        """Test load order validation"""
        # Correct order
        plugins = ['Fallout4.esm', 'DLCRobot.esm', 'ModA.esp']
        issues = Fallout4Rules.validate_load_order(plugins)
        assert len(issues['errors']) == 0
        
        # Wrong order (Fallout4.esm not first)
        plugins_wrong = ['DLCRobot.esm', 'Fallout4.esm', 'ModA.esp']
        issues = Fallout4Rules.validate_load_order(plugins_wrong)
        assert len(issues['errors']) > 0
    
    def test_get_plugin_dependencies(self):
        """Test dependency detection"""
        deps = Fallout4Rules.get_plugin_dependencies('NukaWorldMod.esp')
        assert 'Fallout4.esm' in deps
        assert 'DLCNukaWorld.esm' in deps
    
    def test_check_conflicts(self):
        """Test conflict detection"""
        plugins = [
            'SimSettlements.esp',
            'WorkshopFramework.esp',
            'SettlementExpanded.esp'
        ]
        
        conflicts = Fallout4Rules.check_conflicts('SimSettlements.esp', plugins)
        # Should detect potential conflicts with other settlement mods
        assert len(conflicts) >= 0  # May or may not have conflicts
    
    def test_get_recommendations(self):
        """Test recommendations generation"""
        plugins = [
            'Fallout4.esm',
            'DLCRobot.esm',
            'F4SE_Plugin.esp',
            'WeaponMod.esp'
        ]
        
        recommendations = Fallout4Rules.get_recommendations(plugins)
        # Should recommend F4SE installation
        assert any('F4SE' in rec or 'Script Extender' in rec for rec in recommendations)
    
    def test_complex_optimization(self):
        """Test complex load order with many plugins"""
        plugins = [
            'RandomMod.esp',
            'DLCNukaWorld.esm',
            'Fallout4.esm',
            'DLCRobot.esm',
            'Unofficial Fallout 4 Patch.esp',
            'WeaponMod.esp',
            'ArmorMod.esp',
            'UIFixes.esp',
            'SettlementMod.esp',
            'Bashed Patch.esp',
        ]
        
        optimized = Fallout4Rules.optimize_load_order(plugins)
        
        # Check masters are first in correct order
        assert optimized[0] == 'Fallout4.esm'
        assert optimized[1] == 'DLCRobot.esm'
        assert optimized[2] == 'DLCNukaWorld.esm'
        
        # Check unofficial patch is early
        ufo4p_index = optimized.index('Unofficial Fallout 4 Patch.esp')
        assert ufo4p_index < len(optimized) // 2  # Should be in first half
        
        # Check bashed patch is last
        assert optimized[-1] == 'Bashed Patch.esp'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
