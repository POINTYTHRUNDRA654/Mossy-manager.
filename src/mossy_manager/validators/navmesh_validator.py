"""
Navmesh Validator - Detect deleted or broken navmesh records

CRITICAL: Deleted navmesh (NAVM) records cause instant CTD in Fallout 4.
This is one of the most common and serious issues in FO4 modding.

The standard fix is to "undelete and disable" the records, which this
validator detects so the fixer can apply the repair.
"""

import logging
from pathlib import Path
from typing import List

from mossy_manager.validators.mod_validator import Issue
from mossy_manager.external.plugin_parser import PluginParser

logger = logging.getLogger(__name__)


class NavmeshValidator:
    """
    Validates plugin files for deleted navmesh records.

    Deleted navmesh (NAVM records with deletion flag set) is a CRITICAL
    issue in Fallout 4 that causes instant crash to desktop. This validator
    detects these issues so they can be fixed with the "undelete and disable"
    standard modding practice.
    """

    def __init__(self):
        self.parser = PluginParser()

    def validate(self, plugin_path: Path) -> List[Issue]:
        """
        Check a plugin for deleted navmesh records.

        Args:
            plugin_path: Path to .esp/.esm/.esl file

        Returns:
            List of Issue objects for any deleted navmesh found
        """
        issues = []

        if not plugin_path.exists():
            logger.error(f"Plugin not found: {plugin_path}")
            return issues

        logger.debug(f"Checking {plugin_path.name} for deleted navmesh...")

        try:
            # Check if plugin has any NAVM records at all
            record_types = self.parser.get_record_signatures(plugin_path)

            if 'NAVM' not in record_types:
                logger.debug(f"  No NAVM records in {plugin_path.name}")
                return issues

            logger.info(f"  {plugin_path.name} contains NAVM records, checking for deletions...")

            # Check for deleted NAVM records
            # Note: esplugin has limited support for this, so we log a note
            # For production use, the FO4Edit script will be more accurate
            deleted_navmesh = self.parser.has_deleted_records(plugin_path, "NAVM")

            if deleted_navmesh:
                logger.warning(
                    f"  CRITICAL: {plugin_path.name} has {len(deleted_navmesh)} "
                    f"deleted NAVM record(s)!"
                )

                for record_id in deleted_navmesh:
                    issues.append(Issue(
                        severity="critical",
                        category="navmesh",
                        message=f"Deleted navmesh record: {record_id} (causes CTD)",
                        fix_available=True,
                        fix_data={
                            "record_id": record_id,
                            "record_type": "NAVM",
                            "fix_method": "undelete_and_disable"
                        },
                        plugin_name=plugin_path.name,
                        record_id=record_id
                    ))
            else:
                # Since esplugin detection is limited, we should also note that
                # FO4Edit provides more thorough checking
                logger.info(
                    f"  {plugin_path.name}: No deleted NAVM detected by quick scan. "
                    f"Run with FO4Edit for thorough validation."
                )

                # Add an info-level suggestion to run deep scan
                issues.append(Issue(
                    severity="info",
                    category="navmesh",
                    message=(
                        f"{plugin_path.name} contains NAVM records. "
                        f"Quick scan found no deletions, but run FO4Edit deep scan "
                        f"for 100% accuracy."
                    ),
                    fix_available=False,
                    fix_data={"needs_deep_scan": True},
                    plugin_name=plugin_path.name
                ))

        except Exception as e:
            logger.error(f"Failed to validate navmesh in {plugin_path.name}: {e}")
            issues.append(Issue(
                severity="error",
                category="navmesh",
                message=f"Navmesh validation failed: {e}",
                fix_available=False,
                plugin_name=plugin_path.name
            ))

        return issues

    def validate_deep(self, plugin_path: Path, xedit_integration) -> List[Issue]:
        """
        Perform deep navmesh validation using FO4Edit script.

        This is more thorough than the quick esplugin-based scan and should
        be used when accuracy is critical.

        Args:
            plugin_path: Path to plugin file
            xedit_integration: XEditIntegration instance for running FO4Edit

        Returns:
            List of Issue objects with detailed navmesh problems

        Note:
            This method requires FO4Edit to be installed and the
            DetectDeletedNavmesh.pas script to be available.
        """
        issues = []

        logger.info(f"Running deep navmesh scan with FO4Edit on {plugin_path.name}...")

        try:
            # TODO: Implement FO4Edit script execution
            # This would:
            # 1. Launch FO4Edit with DetectDeletedNavmesh.pas script
            # 2. Parse FO4Edit's output log
            # 3. Extract deleted record IDs
            # 4. Create Issue objects

            logger.warning("Deep navmesh validation not yet implemented")
            logger.warning("Use FO4Edit manually for thorough checking")

        except Exception as e:
            logger.error(f"Deep navmesh scan failed for {plugin_path.name}: {e}")
            issues.append(Issue(
                severity="error",
                category="navmesh",
                message=f"Deep scan failed: {e}",
                fix_available=False,
                plugin_name=plugin_path.name
            ))

        return issues
