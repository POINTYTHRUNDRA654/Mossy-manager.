"""
Mod Organizer 2 Integration Module

Provides functionality to detect, read, and write MO2 configuration files
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, List
import configparser

logger = logging.getLogger(__name__)


class MO2Integration:
    """
    Mod Organizer 2 integration for reading and writing mod configurations
    
    This class provides methods to:
    - Auto-detect MO2 installation
    - Read MO2 profile configurations
    - Read plugin states and load order
    - Write back optimized load orders
    - Detect mod list and enabled mods
    """
    
    # Common MO2 installation paths
    MO2_COMMON_PATHS = [
        Path(os.environ.get('PROGRAMFILES', 'C:/Program Files')) / 'ModOrganizer',
        Path(os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)')) / 'ModOrganizer',
        Path.home() / 'ModOrganizer',
        Path('C:/Modding/ModOrganizer2'),
        Path('C:/Games/ModOrganizer2'),
    ]
    
    def __init__(self, mo2_path: Optional[Path] = None):
        """
        Initialize MO2 integration
        
        Args:
            mo2_path: Path to MO2 installation directory
        """
        self.mo2_path = mo2_path
        self.profiles_path: Optional[Path] = None
        self.mods_path: Optional[Path] = None
        self.current_profile: Optional[str] = None
        
        if mo2_path and mo2_path.exists():
            self._init_paths()
    
    def _init_paths(self):
        """Initialize MO2 directory paths"""
        if self.mo2_path:
            self.profiles_path = self.mo2_path / 'profiles'
            self.mods_path = self.mo2_path / 'mods'
    
    @classmethod
    def detect_mo2_installation(cls) -> Optional[Path]:
        """
        Auto-detect Mod Organizer 2 installation
        
        Returns:
            Path to MO2 directory if found, None otherwise
        """
        logger.info("Attempting to auto-detect MO2 installation")
        
        for path in cls.MO2_COMMON_PATHS:
            if path.exists() and (path / 'ModOrganizer.exe').exists():
                logger.info(f"Found MO2 installation at: {path}")
                return path
        
        logger.warning("Could not auto-detect MO2 installation")
        return None
    
    def detect_game_instance(self, game_name: str = 'Fallout4') -> Optional[Path]:
        """
        Detect MO2 instance for specific game
        
        Args:
            game_name: Name of the game (e.g., 'Fallout4', 'Skyrim')
            
        Returns:
            Path to game instance if found
        """
        if not self.mo2_path:
            self.mo2_path = self.detect_mo2_installation()
            if self.mo2_path:
                self._init_paths()
        
        if not self.mo2_path:
            return None
        
        # Check for portable instance
        portable_path = self.mo2_path / game_name
        if portable_path.exists():
            logger.info(f"Found portable {game_name} instance")
            return portable_path
        
        return self.mo2_path

    def find_tool(self, candidate_names: List[str]) -> Optional[Path]:
        """
        Search inside the MO2 installation for a tool executable.

        Args:
            candidate_names: Possible executable names (e.g., ['FO4Edit.exe']).

        Returns:
            Path to the first match, or None.
        """
        if not self.mo2_path:
            return None

        tool_roots = [self.mo2_path]
        tools_dir = self.mo2_path / 'tools'
        if tools_dir.exists():
            tool_roots.append(tools_dir)

        for root in tool_roots:
            for name in candidate_names:
                candidate = root / name
                if candidate.exists():
                    return candidate

            # Recursive search in tools folder
            if root.is_dir():
                for match in root.rglob('*'):
                    if match.is_file() and match.name in candidate_names:
                        return match

        return None
    
    def list_profiles(self) -> List[str]:
        """
        List available MO2 profiles
        
        Returns:
            List of profile names
        """
        if not self.profiles_path or not self.profiles_path.exists():
            logger.warning("Profiles path not found")
            return []
        
        profiles = []
        for item in self.profiles_path.iterdir():
            if item.is_dir():
                profiles.append(item.name)
        
        logger.info(f"Found {len(profiles)} profiles")
        return profiles
    
    def get_profile_path(self, profile_name: str) -> Optional[Path]:
        """
        Get path to specific profile directory
        
        Args:
            profile_name: Name of the profile
            
        Returns:
            Path to profile directory
        """
        if not self.profiles_path:
            return None
        
        profile_path = self.profiles_path / profile_name
        if profile_path.exists():
            return profile_path
        
        return None
    
    def read_plugins_txt(self, profile_name: str) -> Dict[str, bool]:
        """
        Read plugins.txt from MO2 profile
        
        Args:
            profile_name: Name of the profile
            
        Returns:
            Dictionary mapping plugin names to enabled status
        """
        profile_path = self.get_profile_path(profile_name)
        if not profile_path:
            logger.error(f"Profile not found: {profile_name}")
            return {}
        
        plugins_file = profile_path / 'plugins.txt'
        if not plugins_file.exists():
            logger.warning(f"plugins.txt not found in profile: {profile_name}")
            return {}
        
        plugins = {}
        with open(plugins_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                enabled = line.startswith('*')
                plugin_name = line[1:] if enabled else line
                
                if plugin_name:
                    plugins[plugin_name] = enabled
        
        logger.info(f"Read {len(plugins)} plugins from {profile_name}")
        return plugins
    
    def read_loadorder_txt(self, profile_name: str) -> List[str]:
        """
        Read loadorder.txt from MO2 profile
        
        Args:
            profile_name: Name of the profile
            
        Returns:
            Ordered list of plugin names
        """
        profile_path = self.get_profile_path(profile_name)
        if not profile_path:
            logger.error(f"Profile not found: {profile_name}")
            return []
        
        loadorder_file = profile_path / 'loadorder.txt'
        if not loadorder_file.exists():
            logger.warning(f"loadorder.txt not found in profile: {profile_name}")
            return []
        
        load_order = []
        with open(loadorder_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    load_order.append(line)
        
        logger.info(f"Read {len(load_order)} plugins from loadorder.txt")
        return load_order
    
    def write_plugins_txt(self, profile_name: str, plugins: Dict[str, bool]) -> bool:
        """
        Write plugins.txt to MO2 profile
        
        Args:
            profile_name: Name of the profile
            plugins: Dictionary mapping plugin names to enabled status
            
        Returns:
            True if successful
        """
        profile_path = self.get_profile_path(profile_name)
        if not profile_path:
            logger.error(f"Profile not found: {profile_name}")
            return False
        
        plugins_file = profile_path / 'plugins.txt'
        
        try:
            with open(plugins_file, 'w', encoding='utf-8') as f:
                f.write("# This file was automatically generated by Mossy Manager\n")
                for plugin, enabled in plugins.items():
                    prefix = '*' if enabled else ''
                    f.write(f"{prefix}{plugin}\n")
            
            logger.info(f"Wrote {len(plugins)} plugins to plugins.txt")
            return True
        except Exception as e:
            logger.error(f"Error writing plugins.txt: {e}")
            return False
    
    def write_loadorder_txt(self, profile_name: str, load_order: List[str]) -> bool:
        """
        Write loadorder.txt to MO2 profile
        
        Args:
            profile_name: Name of the profile
            load_order: Ordered list of plugin names
            
        Returns:
            True if successful
        """
        profile_path = self.get_profile_path(profile_name)
        if not profile_path:
            logger.error(f"Profile not found: {profile_name}")
            return False
        
        loadorder_file = profile_path / 'loadorder.txt'
        
        try:
            with open(loadorder_file, 'w', encoding='utf-8') as f:
                f.write("# This file was automatically generated by Mossy Manager\n")
                for plugin in load_order:
                    f.write(f"{plugin}\n")
            
            logger.info(f"Wrote {len(load_order)} plugins to loadorder.txt")
            return True
        except Exception as e:
            logger.error(f"Error writing loadorder.txt: {e}")
            return False
    
    def read_modlist_txt(self, profile_name: str) -> Dict[str, bool]:
        """
        Read modlist.txt to get enabled mods
        
        Args:
            profile_name: Name of the profile
            
        Returns:
            Dictionary mapping mod names to enabled status
        """
        profile_path = self.get_profile_path(profile_name)
        if not profile_path:
            logger.error(f"Profile not found: {profile_name}")
            return {}
        
        modlist_file = profile_path / 'modlist.txt'
        if not modlist_file.exists():
            logger.warning(f"modlist.txt not found in profile: {profile_name}")
            return {}
        
        mods = {}
        with open(modlist_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                enabled = line.startswith('+')
                disabled = line.startswith('-')
                
                if enabled or disabled:
                    mod_name = line[1:]
                    mods[mod_name] = enabled
        
        logger.info(f"Read {len(mods)} mods from modlist.txt")
        return mods
    
    def get_mo2_info(self) -> Dict[str, any]:
        """
        Get comprehensive MO2 installation information
        
        Returns:
            Dictionary with MO2 information
        """
        info = {
            'mo2_path': str(self.mo2_path) if self.mo2_path else None,
            'profiles_path': str(self.profiles_path) if self.profiles_path else None,
            'mods_path': str(self.mods_path) if self.mods_path else None,
            'profiles': self.list_profiles() if self.profiles_path else [],
            'detected': self.mo2_path is not None
        }
        
        return info
