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
        # Steam-library / Nexus Mod Manager common locations
        Path('C:/Games/Mod Organizer 2'),
        Path('C:/Modding/MO2'),
        Path(os.environ.get('LOCALAPPDATA', 'C:/Users/Default/AppData/Local')) / 'ModOrganizer',
        Path(os.environ.get('PROGRAMFILES', 'C:/Program Files')) / 'Mod Organizer 2',
        Path(os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)')) / 'Mod Organizer 2',
    ]
    
    def __init__(self, mo2_path: Optional[Path] = None, game_name: str = 'Fallout 4'):
        """
        Initialize MO2 integration

        Args:
            mo2_path: Path to MO2 installation directory
            game_name: Name of the game (e.g., 'Fallout 4', 'Skyrim Special Edition')
        """
        self.mo2_path = mo2_path
        self.game_name = game_name
        self.profiles_path: Optional[Path] = None
        self.mods_path: Optional[Path] = None
        self.overwrite_path: Optional[Path] = None
        self.download_path: Optional[Path] = None
        self.game_path: Optional[Path] = None
        self.current_profile: Optional[str] = None

        if mo2_path and mo2_path.exists():
            self._init_paths()

    def _init_paths(self):
        """Initialize MO2 directory paths by reading ModOrganizer.ini from AppData (like LOOT does)"""
        if not self.mo2_path:
            return

        # MO2 stores per-game configuration in %LOCALAPPDATA%\ModOrganizer\<GameName>\ModOrganizer.ini
        # This is how LOOT and other tools find MO2 settings
        appdata_mo2 = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')) / 'ModOrganizer' / self.game_name
        ini_file = appdata_mo2 / 'ModOrganizer.ini'

        if not ini_file.exists():
            # Fall back to checking in MO2 installation directory (portable mode)
            ini_file = self.mo2_path / 'ModOrganizer.ini'

        if ini_file.exists():
            config = configparser.ConfigParser()
            try:
                # MO2 uses UTF-8 with BOM, configparser handles this
                config.read(ini_file, encoding='utf-8')
                logger.info(f"Reading MO2 configuration from: {ini_file}")

                # Extract paths from [Settings] section
                if 'Settings' in config:
                    settings = config['Settings']

                    # Profiles directory (where profiles/ folder is)
                    if 'profiles_directory' in settings:
                        self.profiles_path = Path(settings['profiles_directory'])
                        logger.info(f"Found profiles_directory: {self.profiles_path}")

                    # Mods directory (where mods/ folder is)
                    if 'mod_directory' in settings:
                        self.mods_path = Path(settings['mod_directory'])
                        logger.info(f"Found mod_directory: {self.mods_path}")

                    # Overwrite directory
                    if 'overwrite_directory' in settings:
                        self.overwrite_path = Path(settings['overwrite_directory'])
                        logger.info(f"Found overwrite_directory: {self.overwrite_path}")

                    # Download directory
                    if 'download_directory' in settings:
                        self.download_path = Path(settings['download_directory'])

                # Extract game path from [General] section
                if 'General' in config:
                    general = config['General']
                    if 'gamePath' in general:
                        # MO2 stores paths as @ByteArray(...) format, extract the actual path
                        game_path_raw = general['gamePath']
                        if game_path_raw.startswith('@ByteArray('):
                            # Remove @ByteArray( and trailing )
                            game_path_str = game_path_raw[11:-1]
                            # Replace \\  with \
                            game_path_str = game_path_str.replace('\\\\', '\\')
                            self.game_path = Path(game_path_str)
                            logger.info(f"Found gamePath: {self.game_path}")
                        else:
                            self.game_path = Path(game_path_raw)

                # If paths weren't found in INI, fall back to defaults
                if not self.profiles_path:
                    logger.warning("profiles_directory not found in INI, using default")
                    self.profiles_path = self.mo2_path / 'profiles'

                if not self.mods_path:
                    logger.warning("mod_directory not found in INI, using default")
                    self.mods_path = self.mo2_path / 'mods'

            except Exception as e:
                logger.error(f"Could not parse ModOrganizer.ini: {e}", exc_info=True)
                # Fall back to portable mode defaults
                self.profiles_path = self.mo2_path / 'profiles'
                self.mods_path = self.mo2_path / 'mods'
        else:
            # No INI file found, use portable mode defaults
            logger.warning(f"No ModOrganizer.ini found at {ini_file}, using portable defaults")
            self.profiles_path = self.mo2_path / 'profiles'
            self.mods_path = self.mo2_path / 'mods'
    
    @classmethod
    def detect_mo2_installation(cls) -> Optional[Path]:
        """
        Enhanced auto-detect for Mod Organizer 2 installation.

        Checks common install paths, then enumerates all sub-folders in
        %%LOCALAPPDATA%%\\ModOrganizer for a valid ModOrganizer.ini (the same
        strategy used by LOOT), and finally accepts any folder that contains
        ModOrganizer.exe as a valid portable instance.

        Returns:
            Path to MO2 directory if found, None otherwise
        """
        logger.info("Attempting to auto-detect MO2 installation (LOOT-style)")

        # 1. Check all common install paths
        for path in cls.MO2_COMMON_PATHS:
            if path.exists() and (path / 'ModOrganizer.exe').exists():
                logger.info(f"Found MO2 installation at: {path}")
                return path

        # 2. Enumerate all subfolders in %LOCALAPPDATA%\ModOrganizer (like LOOT does)
        localappdata = os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData' / 'Local'))
        modorganizer_root = Path(localappdata) / 'ModOrganizer'
        if modorganizer_root.exists():
            for sub in modorganizer_root.iterdir():
                if sub.is_dir():
                    ini_file = sub / 'ModOrganizer.ini'
                    if ini_file.exists():
                        # Try to extract the install path from the INI
                        try:
                            config = configparser.ConfigParser()
                            config.read(ini_file, encoding='utf-8')
                            if 'General' in config and 'mo2_path' in config['General']:
                                mo2_path = Path(config['General']['mo2_path'])
                                if mo2_path.exists() and (mo2_path / 'ModOrganizer.exe').exists():
                                    logger.info(f"Found MO2 install from INI: {mo2_path}")
                                    return mo2_path
                        except Exception as e:
                            logger.warning(f"Error reading {ini_file}: {e}")
                        # Treat the subfolder itself as a portable instance
                        if (sub / 'ModOrganizer.exe').exists():
                            logger.info(f"Found portable MO2 instance at: {sub}")
                            return sub

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

    def get_game_data_path(self) -> Optional[Path]:
        """
        Get path to game's Data directory (where plugins are located)

        Returns:
            Path to Data directory (e.g., G:/Steam/steamapps/common/Fallout 4/Data)
        """
        if self.game_path and self.game_path.exists():
            data_path = self.game_path / 'Data'
            if data_path.exists():
                return data_path
            logger.warning(f"Data directory not found in game path: {self.game_path}")
        else:
            logger.warning("Game path not set or doesn't exist")
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

    def scan_orphaned_mods(self) -> List[str]:
        """
        Find mods present in the ``mods/`` folder that are not referenced in
        any profile's ``modlist.txt``.

        A mod is considered "orphaned" when it exists on disk but no profile
        has ever added it to its modlist (enabled *or* disabled).  These are
        safe to review for removal to reclaim disk space.

        Returns
        -------
        list of str
            Mod directory names that are orphaned.
        """
        if not self.mods_path or not self.mods_path.exists():
            return []

        # Collect every mod name from every profile's modlist.txt
        referenced: set = set()
        for profile in self.list_profiles():
            modlist = self.read_modlist_txt(profile)
            referenced.update(modlist.keys())

        # Every subdirectory in mods/ is an installed mod
        orphaned = []
        for entry in sorted(self.mods_path.iterdir()):
            if entry.is_dir() and entry.name not in referenced:
                orphaned.append(entry.name)

        logger.info(f"Orphaned mod scan: {len(orphaned)} orphaned out of "
                    f"{sum(1 for e in self.mods_path.iterdir() if e.is_dir())} total")
        return orphaned
