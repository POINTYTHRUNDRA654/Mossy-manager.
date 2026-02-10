"""Tests for Conflict Resolver"""

import pytest
from pathlib import Path
import tempfile
import os

from mossy_manager.core.conflict_resolver import (
    ConflictResolver, Conflict, ConflictType
)


class TestConflict:
    """Test Conflict class"""
    
    def test_conflict_creation(self):
        """Test creating a conflict"""
        conflict = Conflict(
            ConflictType.FILE_OVERRIDE,
            "textures/test.dds",
            ["ModA", "ModB"],
            severity="medium"
        )
        
        assert conflict.conflict_type == ConflictType.FILE_OVERRIDE
        assert conflict.resource == "textures/test.dds"
        assert len(conflict.mods) == 2
        assert conflict.severity == "medium"


class TestConflictResolver:
    """Test ConflictResolver class"""
    
    def test_resolver_creation(self):
        """Test creating a conflict resolver"""
        resolver = ConflictResolver()
        assert resolver.conflicts == []
        assert resolver.mod_files == {}
    
    def test_scan_mod_files(self):
        """Test scanning mod files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_path = Path(tmpdir)
            
            # Create some test files
            (mod_path / "textures").mkdir()
            (mod_path / "textures" / "test.dds").touch()
            (mod_path / "meshes").mkdir()
            (mod_path / "meshes" / "test.nif").touch()
            (mod_path / "scripts").mkdir()
            (mod_path / "scripts" / "test.pex").touch()
            
            resolver = ConflictResolver()
            files = resolver.scan_mod_files("TestMod", mod_path)
            
            assert len(files) == 3
            assert "textures/test.dds" in files or "textures\\test.dds" in files
    
    def test_detect_file_conflicts(self):
        """Test detecting file conflicts"""
        resolver = ConflictResolver()
        
        # Simulate two mods with overlapping files
        resolver.mod_files["ModA"] = {
            "textures/sky.dds",
            "meshes/tree.nif",
            "scripts/init.pex"
        }
        resolver.mod_files["ModB"] = {
            "textures/sky.dds",  # Conflict!
            "meshes/rock.nif",
            "scripts/init.pex"   # Conflict!
        }
        
        conflicts = resolver.detect_file_conflicts()
        
        assert len(conflicts) == 2
        
        # Find the sky.dds conflict
        sky_conflict = next((c for c in conflicts if "sky.dds" in c.resource), None)
        assert sky_conflict is not None
        assert len(sky_conflict.mods) == 2
        assert "ModA" in sky_conflict.mods
        assert "ModB" in sky_conflict.mods
    
    def test_determine_severity(self):
        """Test severity determination"""
        resolver = ConflictResolver()
        
        # Plugin files should be critical
        assert resolver._determine_severity("plugin.esp") == "critical"
        assert resolver._determine_severity("master.esm") == "critical"
        
        # Scripts should be high
        assert resolver._determine_severity("scripts/test.pex") == "high"
        
        # Textures should be medium
        assert resolver._determine_severity("textures/test.dds") == "medium"
        
        # Other files should be low
        assert resolver._determine_severity("readme.txt") == "low"
    
    def test_analyze_conflicts(self):
        """Test analyzing conflicts with load order"""
        resolver = ConflictResolver()
        
        resolver.mod_files["ModA"] = {"test.esp"}
        resolver.mod_files["ModB"] = {"test.esp"}
        resolver.mod_files["ModC"] = {"test.esp"}
        
        load_order = ["ModA", "ModB", "ModC"]
        
        analysis = resolver.analyze_conflicts(load_order)
        
        assert analysis['total_conflicts'] > 0
        assert 'by_severity' in analysis
        assert 'winners' in analysis
        assert 'losers' in analysis
    
    def test_determine_winner(self):
        """Test determining winner based on load order"""
        resolver = ConflictResolver()
        
        mods = ["ModA", "ModB", "ModC"]
        load_order = ["ModA", "ModB", "ModC"]
        
        # Last in load order should win
        winner = resolver._determine_winner(mods, load_order)
        assert winner == "ModC"
        
        # Different order
        load_order = ["ModC", "ModA", "ModB"]
        winner = resolver._determine_winner(mods, load_order)
        assert winner == "ModB"
    
    def test_suggest_resolution(self):
        """Test suggesting resolutions"""
        resolver = ConflictResolver()
        
        # Critical conflict
        critical = Conflict(
            ConflictType.PLUGIN_CONFLICT,
            "plugin.esp",
            ["ModA", "ModB"],
            severity="critical"
        )
        suggestion = resolver.suggest_resolution(critical)
        assert "CRITICAL" in suggestion
        
        # Medium conflict
        medium = Conflict(
            ConflictType.RESOURCE_CONFLICT,
            "texture.dds",
            ["ModA", "ModB"],
            severity="medium"
        )
        suggestion = resolver.suggest_resolution(medium)
        assert "MEDIUM" in suggestion
    
    def test_generate_report(self):
        """Test generating conflict report"""
        resolver = ConflictResolver()
        
        resolver.mod_files["ModA"] = {"test.dds", "test.esp"}
        resolver.mod_files["ModB"] = {"test.dds", "test.esp"}
        
        report = resolver.generate_report()
        
        assert "CONFLICT RESOLUTION REPORT" in report
        assert "test.dds" in report or "test.esp" in report
    
    def test_get_statistics(self):
        """Test getting statistics"""
        resolver = ConflictResolver()
        
        resolver.mod_files["ModA"] = {"critical.esp", "high.pex", "medium.dds"}
        resolver.mod_files["ModB"] = {"critical.esp", "high.pex", "medium.dds"}
        
        stats = resolver.get_statistics()
        
        assert 'total_conflicts' in stats
        assert 'critical' in stats
        assert 'high' in stats
        assert 'medium' in stats
        assert 'low' in stats
        assert stats['mods_scanned'] == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
