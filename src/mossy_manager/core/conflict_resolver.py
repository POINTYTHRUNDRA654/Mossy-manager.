"""
Conflict Resolver for Mod Organizer 2
Detects and helps resolve conflicts between mods
"""

import os
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Types of conflicts between mods"""
    FILE_OVERRIDE = "file_override"  # Same file in multiple mods
    PLUGIN_CONFLICT = "plugin_conflict"  # Plugin record conflicts
    RESOURCE_CONFLICT = "resource_conflict"  # Texture/mesh/sound conflicts
    SCRIPT_CONFLICT = "script_conflict"  # Script conflicts


class Conflict:
    """Represents a conflict between mods"""
    
    def __init__(self, 
                 conflict_type: ConflictType,
                 resource: str,
                 mods: List[str],
                 severity: str = "medium"):
        self.conflict_type = conflict_type
        self.resource = resource
        self.mods = mods
        self.severity = severity  # low, medium, high, critical
        self.resolution: Optional[str] = None
        
    def __repr__(self):
        return (f"Conflict({self.conflict_type.value}, "
                f"{self.resource}, mods={len(self.mods)}, "
                f"severity={self.severity})")


class ConflictResolver:
    """
    Detects and resolves conflicts between mods in Mod Organizer 2
    """
    
    def __init__(self, mo2_mods_path: Optional[Path] = None):
        """
        Initialize the Conflict Resolver
        
        Args:
            mo2_mods_path: Path to MO2 mods directory
        """
        self.mo2_mods_path = mo2_mods_path
        self.conflicts: List[Conflict] = []
        self.mod_files: Dict[str, Set[str]] = {}  # mod_name -> set of files
        
    def scan_mod_files(self, mod_name: str, mod_path: Path) -> Set[str]:
        """
        Scan all files in a mod directory
        
        Args:
            mod_name: Name of the mod
            mod_path: Path to mod directory
            
        Returns:
            Set of relative file paths in the mod
        """
        files = set()
        
        if not mod_path.exists():
            logger.warning(f"Mod path does not exist: {mod_path}")
            return files
            
        for root, dirs, filenames in os.walk(mod_path):
            for filename in filenames:
                full_path = Path(root) / filename
                rel_path = full_path.relative_to(mod_path)
                files.add(str(rel_path))
                
        self.mod_files[mod_name] = files
        logger.info(f"Scanned {mod_name}: {len(files)} files")
        return files
    
    def detect_file_conflicts(self) -> List[Conflict]:
        """
        Detect file conflicts between mods
        
        Returns:
            List of detected conflicts
        """
        logger.info("Detecting file conflicts")
        
        file_to_mods: Dict[str, List[str]] = {}
        
        # Build reverse index: file -> list of mods containing it
        for mod_name, files in self.mod_files.items():
            for file_path in files:
                if file_path not in file_to_mods:
                    file_to_mods[file_path] = []
                file_to_mods[file_path].append(mod_name)
        
        # Find conflicts (files present in multiple mods)
        conflicts = []
        for file_path, mods in file_to_mods.items():
            if len(mods) > 1:
                severity = self._determine_severity(file_path)
                conflict = Conflict(
                    conflict_type=ConflictType.FILE_OVERRIDE,
                    resource=file_path,
                    mods=mods,
                    severity=severity
                )
                conflicts.append(conflict)
        
        logger.info(f"Detected {len(conflicts)} file conflicts")
        return conflicts
    
    def _determine_severity(self, file_path: str) -> str:
        """
        Determine conflict severity based on file type
        
        Args:
            file_path: Relative path to the file
            
        Returns:
            Severity level (low, medium, high, critical)
        """
        file_lower = file_path.lower()
        
        # Critical: Plugin files
        if file_lower.endswith(('.esp', '.esm', '.esl')):
            return "critical"
        
        # High: Scripts and important game files
        if file_lower.endswith(('.pex', '.psc')) or 'scripts' in file_lower:
            return "high"
        
        # Medium: Textures, meshes, sounds
        if file_lower.endswith(('.dds', '.nif', '.wav', '.mp3', '.fuz')):
            return "medium"
        
        # Low: Other files (configs, text files, etc.)
        return "low"
    
    def analyze_conflicts(self, load_order: List[str]) -> Dict[str, any]:
        """
        Analyze detected conflicts in context of load order
        
        Args:
            load_order: Current load order (winner = last in list)
            
        Returns:
            Analysis report dictionary
        """
        logger.info("Analyzing conflicts with load order")
        
        conflicts = self.detect_file_conflicts()
        self.conflicts = conflicts
        
        analysis = {
            'total_conflicts': len(conflicts),
            'by_severity': {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0
            },
            'by_type': {},
            'winners': {},  # file -> winning mod (last in load order)
            'losers': {}    # file -> list of losing mods
        }
        
        # Count by severity
        for conflict in conflicts:
            analysis['by_severity'][conflict.severity] += 1
            
            # Count by type
            type_name = conflict.conflict_type.value
            analysis['by_type'][type_name] = \
                analysis['by_type'].get(type_name, 0) + 1
            
            # Determine winner based on load order
            winner = self._determine_winner(conflict.mods, load_order)
            losers = [mod for mod in conflict.mods if mod != winner]
            
            analysis['winners'][conflict.resource] = winner
            analysis['losers'][conflict.resource] = losers
        
        return analysis
    
    def _determine_winner(self, mods: List[str], load_order: List[str]) -> str:
        """
        Determine which mod wins based on load order
        Last in load order wins
        
        Args:
            mods: List of mods in conflict
            load_order: Current load order
            
        Returns:
            Winning mod name
        """
        # Find the mod that appears last in load order
        max_index = -1
        winner = mods[0]
        
        for mod in mods:
            try:
                index = load_order.index(mod)
                if index > max_index:
                    max_index = index
                    winner = mod
            except ValueError:
                # Mod not in load order, skip it
                continue
        
        return winner
    
    def suggest_resolution(self, conflict: Conflict) -> str:
        """
        Suggest a resolution for a conflict
        
        Args:
            conflict: The conflict to resolve
            
        Returns:
            Suggested resolution string
        """
        if conflict.severity == "critical":
            return (f"CRITICAL: Plugin conflict for {conflict.resource}. "
                   f"Only one mod should provide this plugin. "
                   f"Disable conflicting mods or merge plugins.")
        
        if conflict.severity == "high":
            return (f"HIGH: Script conflict for {conflict.resource}. "
                   f"Verify compatibility and load order. "
                   f"Winner: {conflict.mods[-1]}")
        
        if conflict.severity == "medium":
            return (f"MEDIUM: Resource conflict for {conflict.resource}. "
                   f"Last mod in load order will override. "
                   f"Adjust load order if needed.")
        
        return (f"LOW: Minor conflict for {conflict.resource}. "
               f"Usually safe to ignore.")
    
    def generate_report(self, load_order: Optional[List[str]] = None) -> str:
        """
        Generate a human-readable conflict report
        
        Args:
            load_order: Optional load order for context
            
        Returns:
            Formatted report string
        """
        if not self.conflicts:
            self.conflicts = self.detect_file_conflicts()
        
        report = ["=" * 60]
        report.append("MOSSY MANAGER - CONFLICT RESOLUTION REPORT")
        report.append("=" * 60)
        report.append("")
        
        if not self.conflicts:
            report.append("✓ No conflicts detected!")
            return "\n".join(report)
        
        # Summary
        report.append(f"Total Conflicts: {len(self.conflicts)}")
        report.append("")
        
        # Group by severity
        by_severity = {}
        for conflict in self.conflicts:
            if conflict.severity not in by_severity:
                by_severity[conflict.severity] = []
            by_severity[conflict.severity].append(conflict)
        
        for severity in ['critical', 'high', 'medium', 'low']:
            if severity in by_severity:
                conflicts = by_severity[severity]
                report.append(f"\n{severity.upper()} Severity ({len(conflicts)}):")
                report.append("-" * 40)
                
                for conflict in conflicts[:10]:  # Show first 10
                    report.append(f"\n  Resource: {conflict.resource}")
                    report.append(f"  Conflicting Mods: {', '.join(conflict.mods)}")
                    report.append(f"  Suggestion: {self.suggest_resolution(conflict)}")
                
                if len(conflicts) > 10:
                    report.append(f"\n  ... and {len(conflicts) - 10} more")
        
        return "\n".join(report)
    
    def get_statistics(self) -> Dict[str, int]:
        """Get conflict statistics"""
        if not self.conflicts:
            self.conflicts = self.detect_file_conflicts()
        
        stats = {
            'total_conflicts': len(self.conflicts),
            'critical': sum(1 for c in self.conflicts if c.severity == 'critical'),
            'high': sum(1 for c in self.conflicts if c.severity == 'high'),
            'medium': sum(1 for c in self.conflicts if c.severity == 'medium'),
            'low': sum(1 for c in self.conflicts if c.severity == 'low'),
            'mods_scanned': len(self.mod_files),
        }
        return stats
    
    def export_for_xedit(self) -> List[Dict[str, Any]]:
        """
        Export conflicts in a format suitable for xEdit processing
        
        Returns:
            List of conflict dictionaries formatted for xEdit
        """
        if not self.conflicts:
            self.conflicts = self.detect_file_conflicts()
        
        exported_conflicts = []
        
        for conflict in self.conflicts:
            conflict_dict = {
                'type': conflict.conflict_type.value,
                'resource': conflict.resource,
                'severity': conflict.severity,
                'mods': conflict.mods,
                'resolution': conflict.resolution
            }
            exported_conflicts.append(conflict_dict)
        
        logger.info(f"Exported {len(exported_conflicts)} conflicts for xEdit")
        return exported_conflicts
