"""
Patcher for Mod Organizer 2
Creates and applies patches for mods
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Patch:
    """Represents a patch that can be applied to mods"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.created_at = datetime.now().isoformat()
        self.operations: List[Dict[str, Any]] = []
        self.target_mods: List[str] = []
        
    def add_operation(self, op_type: str, **kwargs):
        """
        Add a patch operation
        
        Args:
            op_type: Type of operation (replace, delete, add, merge)
            **kwargs: Operation-specific parameters
        """
        operation = {
            'type': op_type,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        self.operations.append(operation)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert patch to dictionary for serialization"""
        return {
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at,
            'operations': self.operations,
            'target_mods': self.target_mods
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Patch':
        """Create patch from dictionary"""
        patch = cls(data['name'], data.get('description', ''))
        patch.created_at = data.get('created_at', datetime.now().isoformat())
        patch.operations = data.get('operations', [])
        patch.target_mods = data.get('target_mods', [])
        return patch
    
    def __repr__(self):
        return (f"Patch({self.name}, ops={len(self.operations)}, "
                f"targets={len(self.target_mods)})")


class Patcher:
    """
    Creates and applies patches for mods in Mod Organizer 2
    """
    
    def __init__(self, patches_dir: Optional[Path] = None):
        """
        Initialize the Patcher
        
        Args:
            patches_dir: Directory to store patch files
        """
        self.patches_dir = patches_dir or Path("./patches")
        self.patches_dir.mkdir(parents=True, exist_ok=True)
        self.patches: Dict[str, Patch] = {}
        
    def create_patch(self, name: str, description: str = "") -> Patch:
        """
        Create a new patch
        
        Args:
            name: Patch name
            description: Patch description
            
        Returns:
            New Patch object
        """
        logger.info(f"Creating patch: {name}")
        patch = Patch(name, description)
        self.patches[name] = patch
        return patch
    
    def load_patch(self, filepath: Path) -> Patch:
        """
        Load a patch from file
        
        Args:
            filepath: Path to patch file (.json)
            
        Returns:
            Loaded Patch object
        """
        logger.info(f"Loading patch from {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        patch = Patch.from_dict(data)
        self.patches[patch.name] = patch
        return patch
    
    def save_patch(self, patch: Patch, filepath: Optional[Path] = None) -> Path:
        """
        Save a patch to file
        
        Args:
            patch: Patch to save
            filepath: Optional custom filepath
            
        Returns:
            Path where patch was saved
        """
        if filepath is None:
            filename = f"{patch.name.replace(' ', '_')}.json"
            filepath = self.patches_dir / filename
        
        logger.info(f"Saving patch to {filepath}")
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(patch.to_dict(), f, indent=2)
        
        logger.info(f"Patch saved successfully")
        return filepath
    
    def list_patches(self) -> List[str]:
        """
        List all available patches
        
        Returns:
            List of patch names
        """
        patches = []
        
        if self.patches_dir.exists():
            for filepath in self.patches_dir.glob("*.json"):
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        patches.append(data.get('name', filepath.stem))
                except Exception as e:
                    logger.warning(f"Failed to read patch {filepath}: {e}")
        
        # Add in-memory patches
        patches.extend([name for name in self.patches.keys() 
                       if name not in patches])
        
        return sorted(patches)
    
    def apply_patch(self, patch: Patch, mod_path: Path, 
                   dry_run: bool = False) -> Dict[str, Any]:
        """
        Apply a patch to a mod
        
        Args:
            patch: Patch to apply
            mod_path: Path to mod directory
            dry_run: If True, don't actually modify files
            
        Returns:
            Result dictionary with status and details
        """
        logger.info(f"Applying patch '{patch.name}' to {mod_path} "
                   f"(dry_run={dry_run})")
        
        result = {
            'success': True,
            'applied_operations': 0,
            'failed_operations': 0,
            'errors': []
        }
        
        for operation in patch.operations:
            try:
                self._apply_operation(operation, mod_path, dry_run)
                result['applied_operations'] += 1
            except Exception as e:
                logger.error(f"Failed to apply operation: {e}")
                result['failed_operations'] += 1
                result['errors'].append(str(e))
                result['success'] = False
        
        logger.info(f"Patch application complete: "
                   f"{result['applied_operations']} succeeded, "
                   f"{result['failed_operations']} failed")
        
        return result
    
    def _apply_operation(self, operation: Dict[str, Any], 
                        mod_path: Path, dry_run: bool) -> None:
        """
        Apply a single patch operation
        
        Args:
            operation: Operation dictionary
            mod_path: Path to mod directory
            dry_run: If True, don't actually modify files
        """
        op_type = operation.get('type')
        
        if op_type == 'replace':
            self._apply_replace(operation, mod_path, dry_run)
        elif op_type == 'delete':
            self._apply_delete(operation, mod_path, dry_run)
        elif op_type == 'add':
            self._apply_add(operation, mod_path, dry_run)
        elif op_type == 'merge':
            self._apply_merge(operation, mod_path, dry_run)
        else:
            raise ValueError(f"Unknown operation type: {op_type}")
    
    def _apply_replace(self, operation: Dict[str, Any], 
                      mod_path: Path, dry_run: bool) -> None:
        """Replace file content"""
        target_file = mod_path / operation['file']
        new_content = operation.get('content', '')
        
        logger.info(f"Replace operation on {target_file}")
        
        if not dry_run:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
    
    def _apply_delete(self, operation: Dict[str, Any], 
                     mod_path: Path, dry_run: bool) -> None:
        """Delete a file"""
        target_file = mod_path / operation['file']
        
        logger.info(f"Delete operation on {target_file}")
        
        if not dry_run and target_file.exists():
            target_file.unlink()
    
    def _apply_add(self, operation: Dict[str, Any], 
                  mod_path: Path, dry_run: bool) -> None:
        """Add a new file"""
        target_file = mod_path / operation['file']
        content = operation.get('content', '')
        
        logger.info(f"Add operation on {target_file}")
        
        if not dry_run:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(content)
    
    def _apply_merge(self, operation: Dict[str, Any], 
                    mod_path: Path, dry_run: bool) -> None:
        """Merge content into existing file"""
        target_file = mod_path / operation['file']
        merge_content = operation.get('content', '')
        
        logger.info(f"Merge operation on {target_file}")
        
        if not dry_run:
            existing_content = ""
            if target_file.exists():
                with open(target_file, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
            
            merged_content = existing_content + "\n" + merge_content
            
            target_file.parent.mkdir(parents=True, exist_ok=True)
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(merged_content)
    
    def create_compatibility_patch(self, 
                                   name: str,
                                   mod1: str, 
                                   mod2: str,
                                   conflicts: List[str]) -> Patch:
        """
        Create a compatibility patch between two mods
        
        Args:
            name: Patch name
            mod1: First mod name
            mod2: Second mod name
            conflicts: List of conflicting files
            
        Returns:
            New compatibility patch
        """
        logger.info(f"Creating compatibility patch for {mod1} and {mod2}")
        
        description = (f"Compatibility patch between {mod1} and {mod2}. "
                      f"Resolves {len(conflicts)} conflicts.")
        
        patch = self.create_patch(name, description)
        patch.target_mods = [mod1, mod2]
        
        # For each conflict, create a merge operation
        for conflict_file in conflicts:
            patch.add_operation(
                'merge',
                file=conflict_file,
                content=f"# Merged content from {mod1} and {mod2}\n",
                source_mods=[mod1, mod2]
            )
        
        return patch
    
    def validate_patch(self, patch: Patch, mod_path: Path) -> Dict[str, Any]:
        """
        Validate that a patch can be applied
        
        Args:
            patch: Patch to validate
            mod_path: Path to mod directory
            
        Returns:
            Validation result dictionary
        """
        logger.info(f"Validating patch '{patch.name}' for {mod_path}")
        
        validation = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        for operation in patch.operations:
            op_type = operation.get('type')
            target_file = operation.get('file')
            
            if not target_file:
                validation['errors'].append(
                    f"Operation {op_type} missing 'file' parameter"
                )
                validation['valid'] = False
                continue
            
            file_path = mod_path / target_file
            
            if op_type in ['replace', 'delete', 'merge']:
                if not file_path.exists():
                    validation['warnings'].append(
                        f"Target file does not exist: {target_file}"
                    )
        
        return validation
    
    def get_statistics(self) -> Dict[str, int]:
        """Get patcher statistics"""
        total_operations = sum(len(p.operations) for p in self.patches.values())
        
        stats = {
            'total_patches': len(self.patches),
            'total_operations': total_operations,
            'saved_patches': len(list(self.patches_dir.glob("*.json")))
        }
        return stats
    
    def export_for_xedit(self, patch: Patch) -> Dict[str, Any]:
        """
        Export a patch in xEdit-compatible format
        
        Args:
            patch: Patch object to export
            
        Returns:
            Dictionary formatted for xEdit integration
        """
        logger.info(f"Exporting patch '{patch.name}' for xEdit")
        
        return patch.to_dict()
