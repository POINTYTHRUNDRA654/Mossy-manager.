"""
Mod Manager - Handles mod-related operations
"""

import os
import configparser
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
    
    def _read_modlist(self, profile_name="Default"):
        """Read modlist.txt for the given profile into an ordered list of (prefix, name) tuples."""
        modlist_path = Path(self.mo2_path) / "profiles" / profile_name / "modlist.txt"
        entries = []
        if modlist_path.exists():
            for line in modlist_path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if stripped.startswith("+") or stripped.startswith("-"):
                    entries.append((stripped[0], stripped[1:]))
        return entries, modlist_path

    def _write_modlist(self, entries, modlist_path):
        """Write ordered (prefix, name) entries back to modlist.txt."""
        modlist_path.parent.mkdir(parents=True, exist_ok=True)
        lines = ["# Mod Organizer mod list\n"]
        for prefix, name in entries:
            lines.append(f"{prefix}{name}\n")
        modlist_path.write_text("".join(lines), encoding="utf-8")

    def enable_mod(self, mod_name, profile_name="Default"):
        """Enable a mod by updating modlist.txt.
        
        Args:
            mod_name: Name of the mod to enable
            profile_name: MO2 profile to update (default: Default)
        """
        mod_path = self.mods_path / mod_name
        if not mod_path.exists():
            raise ValueError(f"Mod '{mod_name}' not found")
        
        entries, modlist_path = self._read_modlist(profile_name)
        updated = False
        for i, (prefix, name) in enumerate(entries):
            if name == mod_name:
                entries[i] = ("+", name)
                updated = True
                break
        if not updated:
            entries.insert(0, ("+", mod_name))
        self._write_modlist(entries, modlist_path)
        return True
    
    def disable_mod(self, mod_name, profile_name="Default"):
        """Disable a mod by updating modlist.txt.
        
        Args:
            mod_name: Name of the mod to disable
            profile_name: MO2 profile to update (default: Default)
        """
        mod_path = self.mods_path / mod_name
        if not mod_path.exists():
            raise ValueError(f"Mod '{mod_name}' not found")
        
        entries, modlist_path = self._read_modlist(profile_name)
        updated = False
        for i, (prefix, name) in enumerate(entries):
            if name == mod_name:
                entries[i] = ("-", name)
                updated = True
                break
        if not updated:
            entries.insert(0, ("-", mod_name))
        self._write_modlist(entries, modlist_path)
        return True
    
    def get_mod_info(self, mod_name):
        """Get information about a mod, including meta.ini details if present.
        
        Args:
            mod_name: Name of the mod
            
        Returns:
            Dictionary with mod information
        """
        mod_path = self.mods_path / mod_name
        if not mod_path.exists():
            raise ValueError(f"Mod '{mod_name}' not found")
        
        meta_file = mod_path / "meta.ini"
        info = {
            "name": mod_name,
            "path": str(mod_path),
            "exists": True,
            "has_meta": meta_file.exists(),
        }
        
        if meta_file.exists():
            cfg = configparser.ConfigParser()
            cfg.read(meta_file, encoding="utf-8")
            general = cfg["General"] if "General" in cfg else {}
            if general.get("modid"):
                info["nexus_mod_id"] = general["modid"]
            if general.get("version"):
                info["version"] = general["version"]
            if general.get("newestversion"):
                info["newest_version"] = general["newestversion"]
            if general.get("filename"):
                info["filename"] = general["filename"]
            if general.get("installationfile"):
                info["installation_file"] = general["installationfile"]
        
        info["file_count"] = sum(1 for _ in mod_path.rglob("*") if _.is_file())
        
        return info
