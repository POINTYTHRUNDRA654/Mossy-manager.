"""
Master Dependency Validator - Check for missing master file dependencies

When a plugin requires master files (DLCs, other mods) that aren't installed,
the mod won't load at all in Fallout 4. This validator detects these issues.
"""

import logging
from pathlib import Path
from typing import List, Optional

from mossy_manager.validators.mod_validator import Issue
from mossy_manager.external.plugin_parser import PluginParser

logger = logging.getLogger(__name__)


class MasterDependencyValidator:
    """
    Validates that all required master files are present.

    Master files are ESP/ESM/ESL files that a plugin depends on. If they're
    missing, Fallout 4 won't load the plugin at all. Common masters include:
    - Fallout4.esm (base game)
    - DLC*.esm (DLC files)
    - Other mod plugins

    This validator checks that all masters exist in the Data directory.
    """

    def __init__(self):
        self.parser = PluginParser()

        # Known Fallout 4 official master files
        self.official_masters = {
            "Fallout4.esm",  # Base game
            "DLCRobot.esm",  # Automatron
            "DLCworkshop01.esm",  # Wasteland Workshop
            "DLCCoast.esm",  # Far Harbor
            "DLCworkshop02.esm",  # Contraptions Workshop
            "DLCworkshop03.esm",  # Vault-Tec Workshop
            "DLCNukaWorld.esm",  # Nuka-World
        }

    def validate(self, plugin_path: Path, data_path: Optional[Path] = None) -> List[Issue]:
        """
        Check if all master dependencies are available.

        Args:
            plugin_path: Path to .esp/.esm/.esl file
            data_path: Path to Fallout 4 Data directory. If None, tries to detect.

        Returns:
            List of Issue objects for missing masters
        """
        issues = []

        if not plugin_path.exists():
            logger.error(f"Plugin not found: {plugin_path}")
            return issues

        # Try to determine Data path if not provided
        if data_path is None:
            data_path = self._detect_data_path(plugin_path)
            if data_path is None:
                logger.warning(
                    f"Could not determine Data path for {plugin_path.name}. "
                    f"Skipping master validation."
                )
                issues.append(Issue(
                    severity="warning",
                    category="masters",
                    message="Cannot validate masters: Data path unknown",
                    fix_available=False,
                    plugin_name=plugin_path.name
                ))
                return issues

        logger.debug(f"Checking master dependencies for {plugin_path.name}...")

        try:
            # Parse plugin to get master list
            plugin_info = self.parser.parse_plugin(plugin_path)

            if not plugin_info.masters:
                logger.debug(f"  {plugin_path.name} has no master dependencies")
                return issues

            logger.info(
                f"  {plugin_path.name} requires {len(plugin_info.masters)} master(s): "
                f"{', '.join(plugin_info.masters)}"
            )

            # Check each master
            missing_masters = []
            for master in plugin_info.masters:
                master_path = data_path / master

                if not master_path.exists():
                    missing_masters.append(master)
                    logger.warning(f"    MISSING: {master}")

                    # Determine severity based on whether it's official or mod
                    is_official = master in self.official_masters
                    severity = "critical" if is_official else "error"

                    issues.append(Issue(
                        severity=severity,
                        category="masters",
                        message=f"Missing required master file: {master}",
                        fix_available=False,  # Can't auto-download master files
                        fix_data={
                            "master_name": master,
                            "is_official_dlc": is_official,
                            "suggestion": self._get_suggestion(master)
                        },
                        plugin_name=plugin_path.name
                    ))
                else:
                    logger.debug(f"    Found: {master}")

            if not missing_masters:
                logger.info(f"  All masters present for {plugin_path.name}")

        except Exception as e:
            logger.error(f"Failed to validate masters for {plugin_path.name}: {e}")
            issues.append(Issue(
                severity="error",
                category="masters",
                message=f"Master validation failed: {e}",
                fix_available=False,
                plugin_name=plugin_path.name
            ))

        return issues

    def _detect_data_path(self, plugin_path: Path) -> Optional[Path]:
        """
        Try to determine Fallout 4 Data directory from plugin path.

        Common patterns:
        - MO2: .../ModOrganizer2/mods/ModName/*.esp
        - Vortex: .../Fallout 4/Data/*.esp
        - Manual: .../Fallout 4/Data/*.esp

        Args:
            plugin_path: Path to plugin file

        Returns:
            Path to Data directory, or None if can't determine
        """
        # Check if plugin is in a Data directory
        for parent in plugin_path.parents:
            if parent.name == "Data":
                return parent

        # Check if plugin is in MO2 mod directory
        # In MO2, plugins are in: .../mods/ModName/*.esp
        # We need to go up to MO2 root and check for game path
        for parent in plugin_path.parents:
            if parent.name == "mods":
                # This might be MO2, but we need the actual game Data path
                # For now, we can't reliably determine this
                logger.debug("Plugin appears to be in MO2 mod directory")
                # Try to find ModOrganizer.ini or similar config
                mo2_root = parent.parent
                # This is complex, so for now return None
                # The caller should provide data_path explicitly for MO2
                return None

        # Could not determine
        return None

    def _get_suggestion(self, master_name: str) -> str:
        """
        Get helpful suggestion for missing master.

        Args:
            master_name: Name of missing master file

        Returns:
            Suggestion string for user
        """
        if master_name in self.official_masters:
            dlc_names = {
                "DLCRobot.esm": "Automatron DLC",
                "DLCworkshop01.esm": "Wasteland Workshop DLC",
                "DLCCoast.esm": "Far Harbor DLC",
                "DLCworkshop02.esm": "Contraptions Workshop DLC",
                "DLCworkshop03.esm": "Vault-Tec Workshop DLC",
                "DLCNukaWorld.esm": "Nuka-World DLC",
            }

            if master_name in dlc_names:
                return f"Install {dlc_names[master_name]} from Steam/GOG"
            elif master_name == "Fallout4.esm":
                return "Base game file missing - verify game files integrity"

        # It's a mod master
        return (
            f"Install the mod that provides {master_name}. "
            f"Search Nexus Mods or check the mod's requirements page."
        )

    def get_all_masters_recursive(
        self,
        plugin_path: Path,
        data_path: Path,
        visited: Optional[set] = None
    ) -> List[str]:
        """
        Get all master dependencies recursively (masters of masters).

        This is useful for understanding the full dependency chain.

        Args:
            plugin_path: Path to plugin file
            data_path: Path to Fallout 4 Data directory
            visited: Set of already-visited plugins (for cycle detection)

        Returns:
            List of all master filenames in dependency order
        """
        if visited is None:
            visited = set()

        all_masters = []

        try:
            plugin_info = self.parser.parse_plugin(plugin_path)

            for master in plugin_info.masters:
                if master in visited:
                    # Cycle detected (shouldn't happen in valid plugins)
                    logger.warning(f"Circular dependency detected: {master}")
                    continue

                visited.add(master)
                all_masters.append(master)

                # Recursively get masters of this master
                master_path = data_path / master
                if master_path.exists():
                    sub_masters = self.get_all_masters_recursive(
                        master_path,
                        data_path,
                        visited
                    )
                    all_masters.extend(sub_masters)

        except Exception as e:
            logger.error(f"Failed to get recursive masters for {plugin_path.name}: {e}")

        return all_masters
