"""Tests for Load Order Manager"""

import pytest
from pathlib import Path
import tempfile
import os

from mossy_manager.core.load_order import LoadOrderManager, Plugin


class TestPlugin:
    """Test Plugin class"""
    
    def test_plugin_creation(self):
        """Test creating a plugin"""
        plugin = Plugin("TestMod.esp", enabled=True, priority=1)
        assert plugin.name == "TestMod.esp"
        assert plugin.enabled is True
        assert plugin.priority == 1
        assert plugin.is_master is False
        assert plugin.is_light is False
    
    def test_plugin_master(self):
        """Test master plugin identification"""
        plugin = Plugin("Skyrim.esm")
        assert plugin.is_master is True
        assert plugin.is_light is False
    
    def test_plugin_light(self):
        """Test light plugin identification"""
        plugin = Plugin("Update.esl")
        assert plugin.is_light is True
        assert plugin.is_master is False
    
    def test_plugin_sorting(self):
        """Test plugin sorting"""
        master = Plugin("Master.esm", priority=3)
        light = Plugin("Light.esl", priority=2)
        regular = Plugin("Regular.esp", priority=1)
        
        plugins = [regular, light, master]
        sorted_plugins = sorted(plugins)
        
        assert sorted_plugins[0].is_master
        assert sorted_plugins[1].is_light
        assert not sorted_plugins[2].is_master and not sorted_plugins[2].is_light


class TestLoadOrderManager:
    """Test LoadOrderManager class"""
    
    def test_manager_creation(self):
        """Test creating a load order manager"""
        manager = LoadOrderManager()
        assert manager.plugins == {}
        assert manager._load_order == []
    
    def test_load_plugins_txt(self):
        """Test loading plugins.txt file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("# Comment\n")
            f.write("*Skyrim.esm\n")
            f.write("*Update.esm\n")
            f.write("TestMod.esp\n")
            f.write("*AnotherMod.esp\n")
            temp_path = f.name
        
        try:
            manager = LoadOrderManager()
            manager.load_plugins_txt(Path(temp_path))
            
            assert len(manager.plugins) == 4
            assert "Skyrim.esm" in manager.plugins
            assert manager.plugins["Skyrim.esm"].enabled is True
            assert manager.plugins["TestMod.esp"].enabled is False
        finally:
            os.unlink(temp_path)
    
    def test_save_plugins_txt(self):
        """Test saving plugins.txt file"""
        manager = LoadOrderManager()
        manager.plugins["Master.esm"] = Plugin("Master.esm", enabled=True, priority=1)
        manager.plugins["Mod.esp"] = Plugin("Mod.esp", enabled=False, priority=2)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "plugins.txt"
            manager.save_plugins_txt(output_path)
            
            assert output_path.exists()
            
            # Verify content
            with open(output_path, 'r') as f:
                content = f.read()
                assert "*Master.esm" in content
                assert "Mod.esp" in content
                assert "*Mod.esp" not in content  # Should not have * prefix
    
    def test_enable_disable_plugin(self):
        """Test enabling and disabling plugins"""
        manager = LoadOrderManager()
        manager.plugins["Test.esp"] = Plugin("Test.esp", enabled=False)
        
        assert manager.enable_plugin("Test.esp") is True
        assert manager.plugins["Test.esp"].enabled is True
        
        assert manager.disable_plugin("Test.esp") is True
        assert manager.plugins["Test.esp"].enabled is False
        
        # Test non-existent plugin
        assert manager.enable_plugin("NonExistent.esp") is False
    
    def test_get_enabled_disabled_plugins(self):
        """Test getting enabled and disabled plugins"""
        manager = LoadOrderManager()
        manager.plugins["Enabled1.esp"] = Plugin("Enabled1.esp", enabled=True)
        manager.plugins["Enabled2.esp"] = Plugin("Enabled2.esp", enabled=True)
        manager.plugins["Disabled1.esp"] = Plugin("Disabled1.esp", enabled=False)
        
        enabled = manager.get_enabled_plugins()
        disabled = manager.get_disabled_plugins()
        
        assert len(enabled) == 2
        assert len(disabled) == 1
        assert "Enabled1.esp" in enabled
        assert "Disabled1.esp" in disabled
    
    def test_optimize_load_order(self):
        """Test optimizing load order"""
        manager = LoadOrderManager()
        manager.plugins["Regular.esp"] = Plugin("Regular.esp", priority=1)
        manager.plugins["Master.esm"] = Plugin("Master.esm", priority=2)
        manager.plugins["Light.esl"] = Plugin("Light.esl", priority=3)
        
        optimized = manager.optimize_load_order()
        
        # Masters should be first, then light, then regular
        assert optimized[0] == "Master.esm"
        assert optimized[1] == "Light.esl"
        assert optimized[2] == "Regular.esp"
    
    def test_validate_load_order(self):
        """Test load order validation"""
        manager = LoadOrderManager()
        manager.plugins["Master.esm"] = Plugin("Master.esm", priority=1)
        manager.plugins["Regular.esp"] = Plugin("Regular.esp", priority=2)
        manager._load_order = ["Master.esm", "Regular.esp"]
        
        is_valid, issues = manager.validate_load_order()
        assert is_valid is True
        assert len(issues) == 0
        
        # Create invalid load order (master after regular)
        manager._load_order = ["Regular.esp", "Master.esm"]
        is_valid, issues = manager.validate_load_order()
        assert is_valid is False
        assert len(issues) > 0
    
    def test_get_statistics(self):
        """Test getting statistics"""
        manager = LoadOrderManager()
        manager.plugins["Master.esm"] = Plugin("Master.esm", enabled=True, priority=1)
        manager.plugins["Light.esl"] = Plugin("Light.esl", enabled=True, priority=2)
        manager.plugins["Regular1.esp"] = Plugin("Regular1.esp", enabled=True, priority=3)
        manager.plugins["Regular2.esp"] = Plugin("Regular2.esp", enabled=False, priority=4)
        
        stats = manager.get_statistics()
        
        assert stats['total'] == 4
        assert stats['enabled'] == 3
        assert stats['disabled'] == 1
        assert stats['masters'] == 1
        assert stats['light'] == 1
        assert stats['regular'] == 2


class TestPluginRepr:
    """Test Plugin __repr__ and dependencies attribute"""

    def test_plugin_repr_enabled(self):
        p = Plugin("MyMod.esp", enabled=True, priority=5)
        r = repr(p)
        assert "✓" in r
        assert "MyMod.esp" in r
        assert "005" in r

    def test_plugin_repr_disabled(self):
        p = Plugin("MyMod.esp", enabled=False, priority=2)
        r = repr(p)
        assert "✗" in r

    def test_plugin_dependencies_default_empty(self):
        p = Plugin("MyMod.esp")
        assert p.dependencies == []


class TestLoadOrderManagerExtra:
    """Additional tests for uncovered LoadOrderManager code paths."""

    def test_load_loadorder_txt(self):
        """Test loading load order from loadorder.txt"""
        with tempfile.TemporaryDirectory() as tmpdir:
            lo_file = Path(tmpdir) / "loadorder.txt"
            lo_file.write_text(
                "# Comment\nFallout4.esm\nDLCRobot.esm\nMyMod.esp\n"
            )

            manager = LoadOrderManager()
            manager.load_loadorder_txt(lo_file)

            assert manager._load_order == ["Fallout4.esm", "DLCRobot.esm", "MyMod.esp"]

    def test_load_loadorder_txt_updates_plugin_priority(self):
        """load_loadorder_txt should update priority for already-loaded plugins"""
        with tempfile.TemporaryDirectory() as tmpdir:
            lo_file = Path(tmpdir) / "loadorder.txt"
            lo_file.write_text("Fallout4.esm\nMyMod.esp\n")

            manager = LoadOrderManager()
            manager.plugins["Fallout4.esm"] = Plugin("Fallout4.esm", priority=99)
            manager.plugins["MyMod.esp"] = Plugin("MyMod.esp", priority=99)
            manager.load_loadorder_txt(lo_file)

            assert manager.plugins["Fallout4.esm"].priority == 1
            assert manager.plugins["MyMod.esp"].priority == 2

    def test_load_loadorder_txt_missing_file(self):
        """load_loadorder_txt with missing file should leave _load_order unchanged"""
        manager = LoadOrderManager()
        manager.load_loadorder_txt(Path("/nonexistent/loadorder.txt"))
        assert manager._load_order == []

    def test_save_loadorder_txt(self):
        """Test saving load order to loadorder.txt"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LoadOrderManager()
            manager.plugins["Master.esm"] = Plugin("Master.esm", priority=1)
            manager.plugins["Mod.esp"] = Plugin("Mod.esp", priority=2)
            manager._load_order = ["Master.esm", "Mod.esp"]

            out = Path(tmpdir) / "loadorder.txt"
            manager.save_loadorder_txt(out)

            assert out.exists()
            content = out.read_text()
            assert "Master.esm" in content
            assert "Mod.esp" in content

    def test_set_load_order(self):
        """Test set_load_order updates priorities"""
        manager = LoadOrderManager()
        manager.plugins["Alpha.esp"] = Plugin("Alpha.esp", priority=3)
        manager.plugins["Beta.esm"] = Plugin("Beta.esm", priority=1)

        manager.set_load_order(["Beta.esm", "Alpha.esp"])

        assert manager._load_order == ["Beta.esm", "Alpha.esp"]
        assert manager.plugins["Beta.esm"].priority == 1
        assert manager.plugins["Alpha.esp"].priority == 2

    def test_get_load_order_from_load_order(self):
        """get_load_order returns _load_order copy when set"""
        manager = LoadOrderManager()
        manager._load_order = ["A.esm", "B.esp"]
        order = manager.get_load_order()
        assert order == ["A.esm", "B.esp"]
        # Should be a copy, not the same list
        order.append("C.esp")
        assert len(manager._load_order) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
