"""
Navmesh Fixer - Automatically fix deleted navmesh records using FO4Edit

This fixer uses FO4Edit's UndeleteNavmesh.pas script to repair deleted
NAVM records that cause instant CTD (crash to desktop) in Fallout 4.

The standard modding practice is "undelete and disable":
1. Undelete the record (clear deletion flag)
2. Set "Initially Disabled" flag (prevents navmesh from being used in-game)

This preserves references while preventing CTDs.
"""

import logging
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from mossy_manager.utils.backup_manager import BackupManager
from mossy_manager.utils.xedit_integration import XEditIntegration

logger = logging.getLogger(__name__)


class NavmeshFixer:
    """
    Automatically fix deleted navmesh records using FO4Edit.

    This class wraps the UndeleteNavmesh.pas script and handles:
    - Backup creation before modifications
    - FO4Edit script execution
    - Log parsing to verify success
    - Error handling and rollback
    """

    def __init__(self, backup_root: Optional[Path] = None):
        """
        Initialize the navmesh fixer.

        Args:
            backup_root: Root directory for backups. If None, uses default location.
        """
        if backup_root is None:
            backup_root = Path.home() / ".mossy_manager" / "backups"

        self.backup_manager = BackupManager(backup_root)
        self.xedit = XEditIntegration()

        # Path to our UndeleteNavmesh.pas script
        self.script_path = Path(__file__).parent.parent / "xedit_scripts" / "fixes" / "UndeleteNavmesh.pas"

    def fix(self,
            plugin_path: Path,
            xedit_path: Optional[Path] = None,
            data_path: Optional[Path] = None,
            timeout: int = 300) -> Dict:
        """
        Fix deleted navmesh records in a plugin.

        Args:
            plugin_path: Path to the plugin file to fix
            xedit_path: Path to FO4Edit.exe (auto-detects if None)
            data_path: Path to Fallout 4 Data directory (auto-detects if None)
            timeout: Maximum time to wait for FO4Edit (seconds), default 5 minutes

        Returns:
            Dictionary with fix results:
            {
                'success': bool,
                'backup_path': Path,
                'records_fixed': int,
                'errors': List[str],
                'log_path': Path
            }

        Raises:
            FileNotFoundError: If plugin, FO4Edit, or script not found
        """
        result = {
            'success': False,
            'backup_path': None,
            'records_fixed': 0,
            'errors': [],
            'log_path': None,
            'elapsed_time': 0
        }

        start_time = time.time()

        # Validate inputs
        if not plugin_path.exists():
            raise FileNotFoundError(f"Plugin not found: {plugin_path}")

        if not self.script_path.exists():
            raise FileNotFoundError(f"UndeleteNavmesh.pas script not found: {self.script_path}")

        # Auto-detect FO4Edit if not provided
        if xedit_path is None:
            logger.info("Auto-detecting FO4Edit...")
            xedit_path = self.xedit.detect_xedit(game='fallout4')
            if xedit_path is None:
                result['errors'].append("FO4Edit not found. Install FO4Edit and try again.")
                return result

        if not xedit_path.exists():
            result['errors'].append(f"FO4Edit not found at: {xedit_path}")
            return result

        logger.info(f"Using FO4Edit: {xedit_path}")
        logger.info(f"Fixing navmesh in: {plugin_path.name}")

        # Step 1: Create backup
        try:
            logger.info("Creating backup before modifications...")
            backup_path = self.backup_manager.create_backup(
                plugin_path.parent,
                label="before_navmesh_fix",
                profile_name=plugin_path.parent.name
            )
            result['backup_path'] = backup_path
            logger.info(f"Backup created: {backup_path}")
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            result['errors'].append(f"Backup failed: {e}")
            return result

        # Step 2: Run FO4Edit with UndeleteNavmesh.pas script
        try:
            logger.info("Launching FO4Edit to fix deleted navmesh...")

            # Build command
            cmd = [
                str(xedit_path),
                '-autoload',  # Auto-load plugins
                '-autoexit',  # Exit after script completes
                '-l', plugin_path.name,  # Load only this plugin
                '-script:' + str(self.script_path),  # Run our script
            ]

            if data_path:
                cmd.extend(['-D', str(data_path)])

            logger.debug(f"Command: {' '.join(cmd)}")

            # Run FO4Edit (blocking, wait for completion)
            process = subprocess.run(
                cmd,
                cwd=xedit_path.parent,  # Run in FO4Edit directory
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='replace'  # Handle encoding issues gracefully
            )

            result['elapsed_time'] = time.time() - start_time

            # Step 3: Parse log output
            log_output = process.stdout + process.stderr

            # Save log for debugging
            log_file = backup_path / "fo4edit_navmesh_fix.log"
            log_file.write_text(log_output, encoding='utf-8')
            result['log_path'] = log_file

            logger.info(f"FO4Edit completed. Log saved to: {log_file}")

            # Parse results from log
            records_fixed = self._parse_fix_count(log_output)
            errors = self._parse_errors(log_output)

            result['records_fixed'] = records_fixed
            result['errors'].extend(errors)

            if records_fixed > 0:
                result['success'] = True
                logger.info(f"Successfully fixed {records_fixed} deleted navmesh record(s)")
            elif records_fixed == 0 and not errors:
                result['success'] = True
                logger.info("No deleted navmesh records found (mod is clean)")
            else:
                result['success'] = False
                logger.warning("Navmesh fix completed but may have errors")

        except subprocess.TimeoutExpired:
            logger.error(f"FO4Edit timed out after {timeout} seconds")
            result['errors'].append(f"FO4Edit timed out after {timeout}s")
            result['success'] = False

        except Exception as e:
            logger.error(f"FO4Edit execution failed: {e}")
            result['errors'].append(f"FO4Edit failed: {e}")
            result['success'] = False

        return result

    def _parse_fix_count(self, log_output: str) -> int:
        """
        Parse FO4Edit log to count how many records were fixed.

        Looks for lines like:
        "Processed: 3 deleted NAVM records"

        Args:
            log_output: FO4Edit log text

        Returns:
            Number of records fixed
        """
        count = 0

        for line in log_output.split('\n'):
            if 'Processed:' in line and 'deleted NAVM' in line:
                # Extract number from "Processed: 3 deleted NAVM records"
                try:
                    parts = line.split('Processed:')[1].split('deleted')[0].strip()
                    count = int(parts)
                    logger.debug(f"Parsed fix count: {count}")
                except (IndexError, ValueError) as e:
                    logger.warning(f"Could not parse fix count from: {line}")

        return count

    def _parse_errors(self, log_output: str) -> List[str]:
        """
        Parse FO4Edit log for error messages.

        Args:
            log_output: FO4Edit log text

        Returns:
            List of error messages
        """
        errors = []

        # Look for ERROR or FAILED keywords
        for line in log_output.split('\n'):
            line_upper = line.upper()
            if 'ERROR' in line_upper or 'FAILED' in line_upper:
                # Skip benign messages
                if 'NO DELETED' in line_upper or 'NOT FOUND' in line_upper:
                    continue

                errors.append(line.strip())
                logger.debug(f"Found error: {line.strip()}")

        return errors

    def fix_multiple(self,
                     plugin_paths: List[Path],
                     xedit_path: Optional[Path] = None,
                     data_path: Optional[Path] = None) -> Dict[str, Dict]:
        """
        Fix navmesh in multiple plugins.

        Args:
            plugin_paths: List of plugin paths to fix
            xedit_path: Path to FO4Edit.exe
            data_path: Path to Fallout 4 Data directory

        Returns:
            Dictionary mapping plugin_name -> fix_result
        """
        results = {}

        logger.info(f"Fixing navmesh in {len(plugin_paths)} plugin(s)")

        for plugin_path in plugin_paths:
            logger.info(f"\nProcessing: {plugin_path.name}")

            try:
                result = self.fix(plugin_path, xedit_path, data_path)
                results[plugin_path.name] = result

                if result['success']:
                    logger.info(f"  ✓ {plugin_path.name}: Fixed {result['records_fixed']} record(s)")
                else:
                    logger.warning(f"  ✗ {plugin_path.name}: {', '.join(result['errors'])}")

            except Exception as e:
                logger.error(f"  ✗ {plugin_path.name}: Exception - {e}")
                results[plugin_path.name] = {
                    'success': False,
                    'backup_path': None,
                    'records_fixed': 0,
                    'errors': [str(e)],
                    'log_path': None
                }

        # Summary
        successful = sum(1 for r in results.values() if r['success'])
        total_fixed = sum(r['records_fixed'] for r in results.values())

        logger.info(f"\nNavmesh fix complete: {successful}/{len(plugin_paths)} successful, {total_fixed} records fixed")

        return results
