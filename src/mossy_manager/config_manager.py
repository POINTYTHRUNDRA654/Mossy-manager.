"""
Config Manager - Handles configuration operations
"""

import os
import configparser
from pathlib import Path


class ConfigManager:
    """Manages Mossy Manager configuration"""
    
    def __init__(self, config_file=None):
        """Initialize the config manager
        
        Args:
            config_file: Path to config file (optional)
        """
        if config_file is None:
            # Use user's home directory for config
            config_dir = Path.home() / ".mossy-manager"
            config_dir.mkdir(exist_ok=True)
            self.config_file = config_dir / "config.ini"
        else:
            self.config_file = Path(config_file)
        
        self.config = configparser.ConfigParser()
        
        # Load existing config or create default
        if self.config_file.exists():
            self.config.read(self.config_file)
        else:
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default configuration"""
        self.config["DEFAULT"] = {
            "mo2_path": "",
            "default_profile": "",
            "auto_backup": "false",
            "game": "fallout4",
            "game_path": "",
            "xedit_path": "",
            "bsarch_path": "",
        }
        self._save_config()
    
    def _save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            self.config.write(f)
    
    def get_config(self, key, section="DEFAULT"):
        """Get a configuration value
        
        Args:
            key: Configuration key
            section: Configuration section (default: DEFAULT)
            
        Returns:
            Configuration value or None if not found
        """
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return None
    
    def set_config(self, key, value, section="DEFAULT"):
        """Set a configuration value
        
        Args:
            key: Configuration key
            value: Configuration value
            section: Configuration section (default: DEFAULT)
        """
        if section not in self.config and section != "DEFAULT":
            self.config.add_section(section)
        
        self.config.set(section, key, str(value))
        self._save_config()
    
    def get_all_config(self, section="DEFAULT"):
        """Get all configuration values
        
        Args:
            section: Configuration section (default: DEFAULT)
            
        Returns:
            Dictionary of all configuration values
        """
        if section not in self.config:
            return {}
        
        return dict(self.config.items(section))
    
    def delete_config(self, key, section="DEFAULT"):
        """Delete a configuration value
        
        Args:
            key: Configuration key
            section: Configuration section (default: DEFAULT)
        """
        if section in self.config and key in self.config[section]:
            self.config.remove_option(section, key)
            self._save_config()
            return True
        return False
