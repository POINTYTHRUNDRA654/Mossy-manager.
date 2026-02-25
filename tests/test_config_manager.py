"""Tests for ConfigManager"""

import pytest
from pathlib import Path
import tempfile
import os

from mossy_manager.config_manager import ConfigManager


class TestConfigManager:
    """Test ConfigManager class"""

    def test_manager_creation_with_file(self):
        """Test creating a ConfigManager with an explicit config file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "test_config.ini"
            manager = ConfigManager(config_file)
            assert manager.config_file == config_file

    def test_manager_creation_creates_default_config(self):
        """Test that a fresh ConfigManager creates a default config file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.ini"
            manager = ConfigManager(config_file)
            assert config_file.exists()

    def test_default_config_keys(self):
        """Test that the default config contains expected keys"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.ini"
            manager = ConfigManager(config_file)
            all_cfg = manager.get_all_config()
            assert "mo2_path" in all_cfg
            assert "default_profile" in all_cfg
            assert "auto_backup" in all_cfg

    def test_get_config_existing_key(self):
        """Test getting an existing configuration value"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.ini"
            manager = ConfigManager(config_file)
            value = manager.get_config("auto_backup")
            assert value == "false"

    def test_get_config_missing_key(self):
        """Test getting a missing configuration value returns None"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.ini"
            manager = ConfigManager(config_file)
            value = manager.get_config("nonexistent_key")
            assert value is None

    def test_set_and_get_config(self):
        """Test setting and then retrieving a configuration value"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.ini"
            manager = ConfigManager(config_file)
            manager.set_config("mo2_path", "C:/Games/MO2")
            assert manager.get_config("mo2_path") == "C:/Games/MO2"

    def test_set_config_persists(self):
        """Test that set_config persists to disk"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.ini"
            manager = ConfigManager(config_file)
            manager.set_config("mo2_path", "C:/Modding/MO2")

            # Create a new manager reading the same file
            manager2 = ConfigManager(config_file)
            assert manager2.get_config("mo2_path") == "C:/Modding/MO2"

    def test_get_all_config(self):
        """Test getting all configuration values"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.ini"
            manager = ConfigManager(config_file)
            all_cfg = manager.get_all_config()
            assert isinstance(all_cfg, dict)
            assert len(all_cfg) >= 3

    def test_get_all_config_missing_section(self):
        """Test get_all_config for a section that doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.ini"
            manager = ConfigManager(config_file)
            result = manager.get_all_config(section="NonExistentSection")
            assert result == {}

    def test_delete_config(self):
        """Test deleting a configuration key"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.ini"
            manager = ConfigManager(config_file)
            manager.set_config("temp_key", "temp_value")
            assert manager.get_config("temp_key") == "temp_value"

            result = manager.delete_config("temp_key")
            assert result is True
            assert manager.get_config("temp_key") is None

    def test_delete_config_nonexistent_key(self):
        """Test deleting a key that doesn't exist returns False"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.ini"
            manager = ConfigManager(config_file)
            result = manager.delete_config("nonexistent_key")
            assert result is False

    def test_set_config_custom_section(self):
        """Test setting a config value in a custom section"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.ini"
            manager = ConfigManager(config_file)
            manager.set_config("my_key", "my_value", section="CustomSection")
            value = manager.get_config("my_key", section="CustomSection")
            assert value == "my_value"

    def test_set_config_integer_value_coerced_to_string(self):
        """Test that integer values are coerced to strings"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.ini"
            manager = ConfigManager(config_file)
            manager.set_config("some_number", 42)
            assert manager.get_config("some_number") == "42"

    def test_loads_existing_config(self):
        """Test that ConfigManager loads an existing config file correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.ini"
            # Write a config manually first
            config_file.write_text("[DEFAULT]\nmo2_path = C:/custom/path\n")

            manager = ConfigManager(config_file)
            assert manager.get_config("mo2_path") == "C:/custom/path"

    def test_default_game_is_fallout4(self):
        """Test that the default game is fallout4"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.ini"
            manager = ConfigManager(config_file)
            assert manager.get_config("game") == "fallout4"

    def test_default_game_path_is_empty(self):
        """Test that the default game_path is empty"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.ini"
            manager = ConfigManager(config_file)
            assert manager.get_config("game_path") == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
