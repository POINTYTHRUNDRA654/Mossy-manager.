"""
Load Order Manager for Mod Organizer 2
Handles reading, writing, and managing plugin load orders
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class Plugin:
    """Represents a plugin/mod file"""
    
    def __init__(self, name: str, enabled: bool = True, priority: int = 0):
        self.name = name
        self.enabled = enabled
        self.priority = priority
        self.is_master = name.lower().endswith('.esm')
        self.is_light = name.lower().endswith('.esl')
        self.dependencies: List[str] = []
        
    def __repr__(self):
        status = "✓" if self.enabled else "✗"
        return f"{status} [{self.priority:03d}] {self.name}"
    
    def __lt__(self, other):
        """For sorting plugins"""
        # Masters first, then light plugins, then regular
        if self.is_master != other.is_master:
            return self.is_master
        if self.is_light != other.is_light:
            return self.is_light
        return self.priority < other.priority


class LoadOrderManager:
    """
    Manages plugin load order for Mod Organizer 2
    Reads and writes plugins.txt and loadorder.txt files
    """
    
    def __init__(self, mo2_profile_path: Optional[Path] = None):
        """
        Initialize the Load Order Manager
        
        Args:
            mo2_profile_path: Path to MO2 profile directory
        """
        self.mo2_profile_path = mo2_profile_path
        self.plugins: Dict[str, Plugin] = {}
        self._load_order: List[str] = []
        
    def load_plugins_txt(self, filepath: Path) -> None:
        """
        Load plugins from plugins.txt file
        Format: Each line contains a plugin name, * prefix means enabled
        
        Args:
            filepath: Path to plugins.txt file
        """
        logger.info(f"Loading plugins from {filepath}")
        
        if not filepath.exists():
            logger.warning(f"Plugins file not found: {filepath}")
            return
            
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                enabled = line.startswith('*')
                plugin_name = line[1:] if enabled else line
                
                if plugin_name:
                    self.plugins[plugin_name] = Plugin(
                        name=plugin_name,
                        enabled=enabled,
                        priority=line_num
                    )
                    
        logger.info(f"Loaded {len(self.plugins)} plugins")
    
    def load_loadorder_txt(self, filepath: Path) -> None:
        """
        Load load order from loadorder.txt file
        Format: Each line contains a plugin name in load order
        
        Args:
            filepath: Path to loadorder.txt file
        """
        logger.info(f"Loading load order from {filepath}")
        
        if not filepath.exists():
            logger.warning(f"Load order file not found: {filepath}")
            return
            
        self._load_order = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    self._load_order.append(line)
                    if line in self.plugins:
                        self.plugins[line].priority = len(self._load_order)
                        
        logger.info(f"Loaded load order with {len(self._load_order)} plugins")
    
    def save_plugins_txt(self, filepath: Path) -> None:
        """
        Save current plugins to plugins.txt file
        
        Args:
            filepath: Path to plugins.txt file
        """
        logger.info(f"Saving plugins to {filepath}")
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# Mossy Manager - Plugin List\n")
            for plugin_name in sorted(self.plugins.keys(), 
                                     key=lambda x: self.plugins[x].priority):
                plugin = self.plugins[plugin_name]
                prefix = "*" if plugin.enabled else ""
                f.write(f"{prefix}{plugin_name}\n")
                
        logger.info(f"Saved {len(self.plugins)} plugins")
    
    def save_loadorder_txt(self, filepath: Path) -> None:
        """
        Save current load order to loadorder.txt file
        
        Args:
            filepath: Path to loadorder.txt file
        """
        logger.info(f"Saving load order to {filepath}")
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# Mossy Manager - Load Order\n")
            for plugin_name in self.get_load_order():
                f.write(f"{plugin_name}\n")
                
        logger.info(f"Saved load order with {len(self._load_order)} plugins")
    
    def get_load_order(self) -> List[str]:
        """Get current load order"""
        if self._load_order:
            return self._load_order.copy()
        return sorted(self.plugins.keys(), 
                     key=lambda x: self.plugins[x].priority)
    
    def set_load_order(self, order: List[str]) -> None:
        """
        Set new load order
        
        Args:
            order: List of plugin names in desired order
        """
        self._load_order = order.copy()
        for idx, plugin_name in enumerate(order, 1):
            if plugin_name in self.plugins:
                self.plugins[plugin_name].priority = idx
    
    def optimize_load_order(self) -> List[str]:
        """
        Optimize load order based on plugin types and dependencies
        Masters (.esm) should load first, then light plugins (.esl), 
        then regular plugins (.esp)
        
        Returns:
            Optimized load order
        """
        logger.info("Optimizing load order")
        
        sorted_plugins = sorted(self.plugins.values())
        optimized_order = [p.name for p in sorted_plugins]
        
        self.set_load_order(optimized_order)
        logger.info("Load order optimized")
        
        return optimized_order
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = True
            return True
        return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = False
            return True
        return False
    
    def get_enabled_plugins(self) -> List[str]:
        """Get list of enabled plugins"""
        return [name for name, plugin in self.plugins.items() if plugin.enabled]
    
    def get_disabled_plugins(self) -> List[str]:
        """Get list of disabled plugins"""
        return [name for name, plugin in self.plugins.items() if not plugin.enabled]
    
    def validate_load_order(self) -> Tuple[bool, List[str]]:
        """
        Validate the current load order
        
        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []
        
        # Check if masters are loaded before regular plugins
        found_regular = False
        for plugin_name in self.get_load_order():
            plugin = self.plugins.get(plugin_name)
            if not plugin:
                continue
                
            if plugin.is_master:
                if found_regular:
                    issues.append(
                        f"Master file {plugin_name} loaded after regular plugins"
                    )
            else:
                found_regular = True
        
        # Check for missing plugins
        for plugin_name in self.plugins:
            if plugin_name not in self.get_load_order():
                issues.append(f"Plugin {plugin_name} not in load order")
        
        is_valid = len(issues) == 0
        return is_valid, issues
    
    def get_statistics(self) -> Dict[str, int]:
        """Get statistics about current load order"""
        stats = {
            'total': len(self.plugins),
            'enabled': len(self.get_enabled_plugins()),
            'disabled': len(self.get_disabled_plugins()),
            'masters': sum(1 for p in self.plugins.values() if p.is_master),
            'light': sum(1 for p in self.plugins.values() if p.is_light),
            'regular': sum(1 for p in self.plugins.values() 
                          if not p.is_master and not p.is_light),
        }
        return stats

    def suggest_esl_candidates(
        self, mods_path: Optional[Path] = None, size_limit_kb: int = 512
    ) -> List[Dict]:
        """
        Identify ``.esp`` plugins that could potentially be ESL-flagged to
        free up plugin slots (Fallout 4's 255-slot cap).

        The heuristic uses file size: plugins under *size_limit_kb* KB are
        usually small enough to fall within the ESL record limit of 2048
        new Form IDs.  The suggestion is advisory — users should verify with
        xEdit before flagging.

        Parameters
        ----------
        mods_path : Path, optional
            Root of the MO2 ``mods/`` directory.  When provided, the actual
            ``.esp`` file is located and its size is measured.
        size_limit_kb : int
            File-size threshold in kilobytes (default 512 KB).

        Returns
        -------
        list of dict
            Each entry has keys ``plugin``, ``size_kb`` (or ``None`` when
            the file was not found), and ``reason``.
        """
        candidates = []
        size_limit_bytes = size_limit_kb * 1024

        for name, plugin in self.plugins.items():
            # Only regular .esp plugins count toward the 255-slot cap
            if plugin.is_master or plugin.is_light:
                continue
            if not name.lower().endswith(".esp"):
                continue

            size_bytes: Optional[int] = None
            if mods_path:
                # Search one level deep inside each mod folder
                mods_root = Path(mods_path)
                for mod_dir in mods_root.iterdir():
                    candidate_file = mod_dir / name
                    if candidate_file.is_file():
                        size_bytes = candidate_file.stat().st_size
                        break

            qualifies = size_bytes is None or size_bytes <= size_limit_bytes

            if qualifies:
                size_kb = round(size_bytes / 1024, 1) if size_bytes is not None else None
                reason = (
                    f"File size {size_kb} KB ≤ {size_limit_kb} KB limit"
                    if size_kb is not None
                    else "File size unknown — verify manually before ESL-flagging"
                )
                candidates.append({
                    "plugin": name,
                    "size_kb": size_kb,
                    "reason": reason,
                })

        # Sort: known-small first, then unknowns
        candidates.sort(key=lambda c: (c["size_kb"] is None, c["size_kb"] or 0))
        return candidates
