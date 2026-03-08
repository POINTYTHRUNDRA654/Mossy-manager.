"""
Auto-Fixer Orchestrator - Coordinates all fixers and applies repairs

This class orchestrates the entire fixing process:
1. Groups issues by category
2. Asks for user confirmation (unless --yes flag)
3. Runs fixers in order of severity (critical first)
4. Creates backups before ALL modifications
5. Reports results

Supported fix categories:
- navmesh: Deleted navmesh records (CRITICAL - causes CTD)
- masters: Missing master files (cannot auto-fix, provides guidance)
- precombines: Broken precombined meshes (future)
- nifs: Missing NIF mesh files (future)
- ba2: Corrupted BA2 archives (future)
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict

from mossy_manager.validators.mod_validator import Issue, ValidationResult
from mossy_manager.fixers.navmesh_fixer import NavmeshFixer

logger = logging.getLogger(__name__)


class AutoFixer:
    """
    Orchestrates automatic fixing of mod issues.

    This class coordinates all the individual fixers and handles:
    - User confirmations
    - Dry-run mode
    - Backup verification
    - Fix ordering by severity
    - Result reporting
    """

    def __init__(self, dry_run: bool = False, skip_confirmations: bool = False):
        """
        Initialize the auto-fixer.

        Args:
            dry_run: If True, show what would be fixed without actually fixing
            skip_confirmations: If True, skip asking for confirmation (dangerous!)
        """
        self.dry_run = dry_run
        self.skip_confirmations = skip_confirmations

        # Initialize fixers
        self.navmesh_fixer = NavmeshFixer()
        # TODO: Add other fixers as they're implemented
        # self.nif_fixer = NIFFixer()
        # self.precombine_fixer = PrecombineFixer()
        # self.ba2_fixer = BA2Fixer()

    def fix_mod(self,
                mod_path: Path,
                issues: List[Issue],
                xedit_path: Optional[Path] = None,
                data_path: Optional[Path] = None) -> Dict[str, Dict]:
        """
        Apply fixes for all detected issues in a mod.

        Args:
            mod_path: Path to mod directory
            issues: List of Issue objects to fix
            xedit_path: Path to FO4Edit (for navmesh fixes)
            data_path: Path to Fallout 4 Data directory

        Returns:
            Dictionary mapping category -> fix_result
            {
                'navmesh': {'success': True, 'records_fixed': 3, ...},
                'masters': {'success': False, 'message': 'Cannot auto-fix', ...}
            }
        """
        logger.info(f"{'[DRY RUN] ' if self.dry_run else ''}Fixing issues in: {mod_path.name}")
        logger.info(f"Total issues to fix: {len(issues)}")

        results = {}

        # Filter to only fixable issues
        fixable_issues = [issue for issue in issues if issue.fix_available]

        if not fixable_issues:
            logger.info("No fixable issues found")
            return results

        logger.info(f"Fixable issues: {len(fixable_issues)}")

        # Group issues by category
        issues_by_category = self._group_issues(fixable_issues)

        # Fix in order of severity: critical first, then error, then warning
        # Within each severity, order by category priority
        category_priority = ['navmesh', 'masters', 'precombines', 'nifs', 'ba2']

        for category in category_priority:
            if category not in issues_by_category:
                continue

            category_issues = issues_by_category[category]

            logger.info(f"\n{'='*60}")
            logger.info(f"Category: {category.upper()} ({len(category_issues)} issues)")
            logger.info(f"{'='*60}")

            # Show issues
            for issue in category_issues:
                severity_symbol = {
                    'critical': '\u2620',  # Skull
                    'error': '\u2717',  # X mark
                    'warning': '\u26A0',  # Warning sign
                    'info': 'ℹ'  # Info
                }.get(issue.severity, '?')

                logger.info(f"  {severity_symbol} [{issue.severity.upper()}] {issue.message}")

            # Confirm with user (unless skip_confirmations)
            if not self.skip_confirmations and not self.dry_run:
                if not self._confirm_fix(category, category_issues):
                    logger.info(f"Skipping {category} fixes (user declined)")
                    results[category] = {
                        'success': False,
                        'skipped': True,
                        'message': 'User declined to fix'
                    }
                    continue

            # Run the appropriate fixer
            if self.dry_run:
                logger.info(f"[DRY RUN] Would fix {len(category_issues)} {category} issues")
                results[category] = {
                    'success': True,
                    'dry_run': True,
                    'issues_count': len(category_issues)
                }
            else:
                results[category] = self._run_fixer(
                    category,
                    category_issues,
                    mod_path,
                    xedit_path,
                    data_path
                )

        # Summary
        logger.info(f"\n{'='*60}")
        logger.info(f"{'[DRY RUN] ' if self.dry_run else ''}Fix Summary")
        logger.info(f"{'='*60}")

        for category, result in results.items():
            if result.get('success'):
                if result.get('dry_run'):
                    logger.info(f"  {category}: Would fix {result.get('issues_count', 0)} issues")
                else:
                    logger.info(f"  {category}: Fixed successfully")
            elif result.get('skipped'):
                logger.info(f"  {category}: Skipped")
            else:
                logger.warning(f"  {category}: FAILED - {result.get('message', 'Unknown error')}")

        return results

    def _group_issues(self, issues: List[Issue]) -> Dict[str, List[Issue]]:
        """
        Group issues by category.

        Args:
            issues: List of Issue objects

        Returns:
            Dictionary mapping category -> list of issues
        """
        grouped = defaultdict(list)

        for issue in issues:
            grouped[issue.category].append(issue)

        return dict(grouped)

    def _confirm_fix(self, category: str, issues: List[Issue]) -> bool:
        """
        Ask user to confirm fix for a category.

        Args:
            category: Issue category (navmesh, masters, etc.)
            issues: List of issues in this category

        Returns:
            True if user confirms, False otherwise
        """
        # Describe what will happen
        descriptions = {
            'navmesh': (
                "This will launch FO4Edit and run the 'Undelete and Disable' "
                "script to fix deleted navmesh records. A backup will be created first."
            ),
            'masters': (
                "Missing master files cannot be automatically fixed. "
                "You must manually install the required DLCs or mods."
            ),
            'precombines': (
                "This will regenerate precombined meshes using FO4Edit. "
                "This can take 10+ minutes for large mods. A backup will be created first."
            ),
            'nifs': (
                "This will attempt to download missing NIF files from Nexus Mods "
                "(requires API key). A backup will be created first."
            ),
            'ba2': (
                "This will attempt to extract and repack corrupted BA2 archives. "
                "A backup will be created first."
            )
        }

        print(f"\nFix {category.upper()} issues?")
        print(f"Issues to fix: {len(issues)}")
        print(f"What will happen: {descriptions.get(category, 'Unknown')}")
        print()

        response = input("Apply fixes? [y/N]: ").strip().lower()
        return response in ['y', 'yes']

    def _run_fixer(self,
                   category: str,
                   issues: List[Issue],
                   mod_path: Path,
                   xedit_path: Optional[Path],
                   data_path: Optional[Path]) -> Dict:
        """
        Run the appropriate fixer for a category of issues.

        Args:
            category: Issue category
            issues: Issues to fix
            mod_path: Mod directory path
            xedit_path: FO4Edit path
            data_path: Fallout 4 Data path

        Returns:
            Fix result dictionary
        """
        logger.info(f"Running fixer for category: {category}")

        try:
            if category == 'navmesh':
                return self._fix_navmesh(issues, mod_path, xedit_path, data_path)

            elif category == 'masters':
                # Cannot auto-fix missing masters
                return {
                    'success': False,
                    'message': 'Missing masters cannot be auto-fixed',
                    'manual_steps': self._get_master_fix_steps(issues)
                }

            # TODO: Implement other fixers
            # elif category == 'precombines':
            #     return self._fix_precombines(issues, mod_path, xedit_path, data_path)
            #
            # elif category == 'nifs':
            #     return self._fix_nifs(issues, mod_path)
            #
            # elif category == 'ba2':
            #     return self._fix_ba2(issues, mod_path)

            else:
                return {
                    'success': False,
                    'message': f'Fixer for {category} not yet implemented'
                }

        except Exception as e:
            logger.error(f"Fixer failed for {category}: {e}")
            return {
                'success': False,
                'message': f'Fixer exception: {e}'
            }

    def _fix_navmesh(self,
                     issues: List[Issue],
                     mod_path: Path,
                     xedit_path: Optional[Path],
                     data_path: Optional[Path]) -> Dict:
        """
        Fix navmesh issues using FO4Edit.

        Args:
            issues: Navmesh issues
            mod_path: Mod directory
            xedit_path: FO4Edit path
            data_path: Fallout 4 Data path

        Returns:
            Fix result
        """
        # Get unique plugin names from issues
        plugins = set()
        for issue in issues:
            if issue.plugin_name:
                plugins.add(issue.plugin_name)

        if not plugins:
            return {
                'success': False,
                'message': 'No plugins identified in issues'
            }

        logger.info(f"Fixing navmesh in {len(plugins)} plugin(s): {', '.join(plugins)}")

        # Fix each plugin
        plugin_paths = [mod_path / plugin_name for plugin_name in plugins]

        try:
            results = self.navmesh_fixer.fix_multiple(
                plugin_paths,
                xedit_path=xedit_path,
                data_path=data_path
            )

            # Aggregate results
            total_fixed = sum(r.get('records_fixed', 0) for r in results.values())
            all_successful = all(r.get('success', False) for r in results.values())
            any_successful = any(r.get('success', False) for r in results.values())

            return {
                'success': all_successful,
                'partial_success': any_successful and not all_successful,
                'records_fixed': total_fixed,
                'plugins_processed': len(results),
                'plugin_results': results
            }

        except Exception as e:
            logger.error(f"Navmesh fix failed: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def _get_master_fix_steps(self, issues: List[Issue]) -> List[str]:
        """
        Generate manual fix steps for missing masters.

        Args:
            issues: Master dependency issues

        Returns:
            List of step-by-step instructions
        """
        steps = []

        for issue in issues:
            master_name = issue.fix_data.get('master_name', 'Unknown')
            is_official = issue.fix_data.get('is_official_dlc', False)
            suggestion = issue.fix_data.get('suggestion', '')

            if is_official:
                steps.append(f"Install official DLC: {master_name} - {suggestion}")
            else:
                steps.append(f"Install mod: {master_name} - {suggestion}")

        return steps
