"""
Mod Manager - Handles mod-related operations
"""

import os
from pathlib import Path


class ModManager:
    """Manages Mod Organizer 2 mods"""
    
    def __init__(self, mo2_path=None):
        """Initialize the mod manager
        
        Args:
            mo2_path: Path to MO2 installation (optional)
        """
        self.mo2_path = mo2_path or os.getcwd()
        self.mods_path = Path(self.mo2_path) / "mods"
        
    def list_mods(self):
        """List all available mods
        
        Returns:
            List of mod names
        """
        if not self.mods_path.exists():
            return []
        
        mods = []
        for item in self.mods_path.iterdir():
            if item.is_dir():
                mods.append(item.name)
        
        return sorted(mods)
    
    def enable_mod(self, mod_name):
        """Enable a mod
        
        Args:
            mod_name: Name of the mod to enable
        """
        mod_path = self.mods_path / mod_name
        if not mod_path.exists():
            raise ValueError(f"Mod '{mod_name}' not found")
        
        # In MO2, mods starting with "+" are typically enabled
        # This is a simplified implementation
        print(f"Enabling mod: {mod_name}")
        return True
    
    def disable_mod(self, mod_name):
        """Disable a mod
        
        Args:
            mod_name: Name of the mod to disable
        """
        mod_path = self.mods_path / mod_name
        if not mod_path.exists():
            raise ValueError(f"Mod '{mod_name}' not found")
        
        print(f"Disabling mod: {mod_name}")
        return True
    
    def get_mod_info(self, mod_name):
        """Get information about a mod
        
        Args:
            mod_name: Name of the mod
            
        Returns:
            Dictionary with mod information
        """
        mod_path = self.mods_path / mod_name
        if not mod_path.exists():
            raise ValueError(f"Mod '{mod_name}' not found")
        
        # Check for meta.ini file
        meta_file = mod_path / "meta.ini"
        info = {
            "name": mod_name,
            "path": str(mod_path),
            "exists": True,
        }
        
        if meta_file.exists():
            info["has_meta"] = True
        else:
            info["has_meta"] = False
        
        # Count files
        file_count = sum(1 for _ in mod_path.rglob("*") if _.is_file())
        info["file_count"] = file_count
        
        return info
