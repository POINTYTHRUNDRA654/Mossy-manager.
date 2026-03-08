"""
Mod Validator - Main orchestrator for Fallout 4 mod validation

This module coordinates all validation checks and provides the main API
for scanning mods for issues. It defines the data models for issues and
validation results.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class Issue:
    """
    Represents a single issue found in a mod.

    Attributes:
        severity: "critical" (CTD), "error" (broken), "warning" (sub-optimal), "info"
        category: "navmesh", "precombines", "nifs", "ba2", "masters"
        message: Human-readable description of the issue
        fix_available: Whether an automatic fix exists for this issue
        fix_data: Additional data needed by the fixer (form IDs, file paths, etc.)
        plugin_name: Name of plugin file where issue was found (if applicable)
        record_id: Form ID or record identifier (if applicable)
    """
    severity: str
    category: str
    message: str
    fix_available: bool = False
    fix_data: Dict = field(default_factory=dict)
    plugin_name: Optional[str] = None
    record_id: Optional[str] = None

    def __post_init__(self):
        """Validate issue data"""
        valid_severities = {"critical", "error", "warning", "info"}
        if self.severity not in valid_severities:
            raise ValueError(
                f"Invalid severity '{self.severity}'. "
                f"Must be one of: {valid_severities}"
            )

        valid_categories = {"navmesh", "precombines", "nifs", "ba2", "masters"}
        if self.category not in valid_categories:
            raise ValueError(
                f"Invalid category '{self.category}'. "
                f"Must be one of: {valid_categories}"
            )

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "fix_available": self.fix_available,
            "fix_data": self.fix_data,
            "plugin_name": self.plugin_name,
            "record_id": self.record_id,
        }


@dataclass
class ValidationResult:
    """
    Result of validating a mod.

    Attributes:
        mod_name: Name of the mod (directory name)
        mod_path: Full path to mod directory
        issues: List of issues found
        timestamp: When validation was performed
        checks_performed: Which validators were run
        plugins_checked: List of plugin files that were validated
    """
    mod_name: str
    mod_path: Path
    issues: List[Issue] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    checks_performed: Set[str] = field(default_factory=set)
    plugins_checked: List[str] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        """Returns True if any issues were found"""
        return len(self.issues) > 0

    @property
    def critical_count(self) -> int:
        """Count of critical issues (cause CTD)"""
        return sum(1 for issue in self.issues if issue.severity == "critical")

    @property
    def error_count(self) -> int:
        """Count of errors (broken functionality)"""
        return sum(1 for issue in self.issues if issue.severity == "error")

    @property
    def warning_count(self) -> int:
        """Count of warnings (sub-optimal)"""
        return sum(1 for issue in self.issues if issue.severity == "warning")

    @property
    def fixable_count(self) -> int:
        """Count of issues that can be auto-fixed"""
        return sum(1 for issue in self.issues if issue.fix_available)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "mod_name": self.mod_name,
            "mod_path": str(self.mod_path),
            "issues": [issue.to_dict() for issue in self.issues],
            "timestamp": self.timestamp.isoformat(),
            "checks_performed": list(self.checks_performed),
            "plugins_checked": self.plugins_checked,
            "summary": {
                "total_issues": len(self.issues),
                "critical": self.critical_count,
                "errors": self.error_count,
                "warnings": self.warning_count,
                "fixable": self.fixable_count,
            }
        }


class ModValidator:
    """
    Main orchestrator for mod validation.

    This class coordinates all the individual validators (navmesh, precombines,
    NIFs, BA2, masters) and provides a unified API for validating mods.

    Example:
        validator = ModValidator()
        result = validator.validate_mod(
            mod_path=Path("/path/to/mod"),
            checks=['navmesh', 'masters']
        )
        if result.has_issues:
            for issue in result.issues:
                print(f"{issue.severity}: {issue.message}")
    """

    def __init__(self):
        """Initialize the validator with all sub-validators"""
        # Import validators here to avoid circular imports
        from mossy_manager.validators.navmesh_validator import NavmeshValidator
        from mossy_manager.validators.master_dependency_validator import MasterDependencyValidator

        self.navmesh_validator = NavmeshValidator()
        self.master_validator = MasterDependencyValidator()
        # TODO: Add other validators as they're implemented
        # self.precombine_validator = PrecombineValidator()
        # self.nif_validator = NIFValidator()
        # self.ba2_validator = BA2Validator()

    def validate_mod(
        self,
        mod_path: Path,
        checks: List[str] = None,
        data_path: Path = None
    ) -> ValidationResult:
        """
        Validate a mod for common Fallout 4 issues.

        Args:
            mod_path: Path to mod directory
            checks: List of checks to perform. If None, runs all checks.
                   Valid values: 'navmesh', 'precombines', 'nifs', 'ba2', 'masters'
            data_path: Path to Fallout 4 Data directory (for master file validation)

        Returns:
            ValidationResult with all issues found

        Raises:
            FileNotFoundError: If mod_path doesn't exist
        """
        if not mod_path.exists():
            raise FileNotFoundError(f"Mod path not found: {mod_path}")

        if not mod_path.is_dir():
            raise ValueError(f"Not a directory: {mod_path}")

        # Default to all checks if not specified
        if checks is None:
            checks = ['navmesh', 'precombines', 'nifs', 'ba2', 'masters']

        logger.info(f"Validating mod: {mod_path.name}")
        logger.info(f"Running checks: {', '.join(checks)}")

        result = ValidationResult(
            mod_name=mod_path.name,
            mod_path=mod_path,
            checks_performed=set(checks)
        )

        # Find all plugin files in the mod
        plugins = list(mod_path.glob("*.esp")) + \
                 list(mod_path.glob("*.esm")) + \
                 list(mod_path.glob("*.esl"))

        if not plugins:
            logger.info(f"No plugin files found in {mod_path.name}")
            return result

        result.plugins_checked = [p.name for p in plugins]
        logger.info(f"Found {len(plugins)} plugin(s): {', '.join(result.plugins_checked)}")

        # Run each validator
        if 'navmesh' in checks:
            logger.info("Running navmesh validator...")
            for plugin in plugins:
                issues = self.navmesh_validator.validate(plugin)
                result.issues.extend(issues)
                logger.info(f"  {plugin.name}: {len(issues)} navmesh issues")

        if 'masters' in checks:
            logger.info("Running master dependency validator...")
            for plugin in plugins:
                issues = self.master_validator.validate(plugin, data_path)
                result.issues.extend(issues)
                logger.info(f"  {plugin.name}: {len(issues)} missing masters")

        # TODO: Add other validators
        # if 'precombines' in checks:
        #     issues = self.precombine_validator.validate(mod_path)
        #     result.issues.extend(issues)
        #
        # if 'nifs' in checks:
        #     issues = self.nif_validator.validate(mod_path)
        #     result.issues.extend(issues)
        #
        # if 'ba2' in checks:
        #     issues = self.ba2_validator.validate(mod_path)
        #     result.issues.extend(issues)

        logger.info(
            f"Validation complete: {len(result.issues)} issues found "
            f"({result.critical_count} critical, {result.error_count} errors, "
            f"{result.warning_count} warnings)"
        )

        return result

    def validate_multiple_mods(
        self,
        mod_paths: List[Path],
        checks: List[str] = None,
        data_path: Path = None
    ) -> Dict[str, ValidationResult]:
        """
        Validate multiple mods at once.

        Args:
            mod_paths: List of mod directory paths
            checks: List of checks to perform
            data_path: Path to Fallout 4 Data directory

        Returns:
            Dictionary mapping mod_name -> ValidationResult
        """
        results = {}

        for mod_path in mod_paths:
            try:
                result = self.validate_mod(mod_path, checks, data_path)
                results[mod_path.name] = result
            except Exception as e:
                logger.error(f"Failed to validate {mod_path.name}: {e}")
                # Create error result
                results[mod_path.name] = ValidationResult(
                    mod_name=mod_path.name,
                    mod_path=mod_path,
                    issues=[Issue(
                        severity="error",
                        category="validation",
                        message=f"Validation failed: {e}",
                        fix_available=False
                    )]
                )

        return results
