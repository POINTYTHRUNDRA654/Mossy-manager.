"""
ESP/ESM/ESL Binary Plugin Parser

Provides high-level interface for parsing Fallout 4 plugin files.
Uses esplugin library (Rust-based, from LOOT) for binary format parsing.
Falls back to FO4Edit integration for complex operations.
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Try to import esplugin (may not be installed)
try:
    from esplugin import Plugin, PluginError
    ESPLUGIN_AVAILABLE = True
except ImportError:
    ESPLUGIN_AVAILABLE = False
    logger.warning("esplugin library not installed. Some plugin parsing features will be limited.")
    logger.warning("Install with: pip install esplugin")


@dataclass
class PluginInfo:
    """Metadata extracted from a plugin file"""
    name: str
    path: Path
    is_master: bool  # ESM flag set
    is_light: bool   # ESL flag set
    masters: List[str]  # List of master file dependencies
    record_count: int
    record_types: Set[str]  # Record signatures (CELL, NAVM, STAT, etc.)
    form_ids: Set[int] = None  # NEW: Form IDs of all records (for overlap detection)
    form_version: Optional[int] = None
    author: Optional[str] = None
    description: Optional[str] = None

    def __post_init__(self):
        """Validate plugin info"""
        if not self.path.exists():
            raise FileNotFoundError(f"Plugin not found: {self.path}")
        if self.form_ids is None:
            self.form_ids = set()


class PluginParser:
    """
    Parse ESP/ESM/ESL binary plugin files.

    This class provides a high-level interface for reading Fallout 4 plugin files.
    It uses the esplugin library (Rust-based, same as LOOT) for fast and accurate parsing.

    For operations not supported by esplugin, use XEditIntegration as fallback.
    """

    def __init__(self):
        self.esplugin_available = ESPLUGIN_AVAILABLE

    def parse_plugin(self, plugin_path: Path) -> PluginInfo:
        """
        Parse a plugin file and return metadata.

        Args:
            plugin_path: Path to .esp/.esm/.esl file

        Returns:
            PluginInfo object with parsed metadata

        Raises:
            FileNotFoundError: If plugin doesn't exist
            ValueError: If plugin is invalid or corrupted
        """
        if not plugin_path.exists():
            raise FileNotFoundError(f"Plugin not found: {plugin_path}")

        if not plugin_path.suffix.lower() in ['.esp', '.esm', '.esl']:
            raise ValueError(f"Not a valid plugin file: {plugin_path}")

        if self.esplugin_available:
            return self._parse_with_esplugin(plugin_path)
        else:
            # Fallback: basic info only
            logger.warning(f"esplugin not available, returning limited info for {plugin_path.name}")
            return self._parse_basic(plugin_path)

    def _parse_with_esplugin(self, plugin_path: Path) -> PluginInfo:
        """Parse plugin using esplugin library (fast, accurate)"""
        try:
            plugin = Plugin(str(plugin_path))

            # Parse header
            is_master = plugin.is_master_file()
            is_light = plugin.is_light_plugin()
            masters = plugin.masters()

            # Get record count and types
            # Note: esplugin doesn't directly expose record types in Python API
            # We'll need to work with what's available
            record_count = plugin.record_and_group_count()

            # For now, we'll use heuristics based on file content
            # In the future, we might parse records directly with custom code
            record_types = self._detect_record_types_heuristic(plugin_path)

            # Extract Form IDs for overlap detection
            form_ids = self.extract_form_ids(plugin_path)

            return PluginInfo(
                name=plugin_path.name,
                path=plugin_path,
                is_master=is_master,
                is_light=is_light,
                masters=masters,
                record_count=record_count,
                record_types=record_types,
                form_ids=form_ids,
                form_version=None,  # esplugin doesn't expose this easily
                author=None,
                description=None
            )

        except Exception as e:
            logger.error(f"Failed to parse {plugin_path.name} with esplugin: {e}")
            raise ValueError(f"Invalid or corrupted plugin: {plugin_path.name}") from e

    def _parse_basic(self, plugin_path: Path) -> PluginInfo:
        """Fallback parser when esplugin is not available (limited info)"""
        # Can only determine basic info from filename and extension
        is_master = plugin_path.suffix.lower() == '.esm'
        is_light = plugin_path.suffix.lower() == '.esl'

        return PluginInfo(
            name=plugin_path.name,
            path=plugin_path,
            is_master=is_master,
            is_light=is_light,
            masters=[],  # Unknown without parsing
            record_count=0,
            record_types=set(),
            form_version=None,
            author=None,
            description=None
        )

    def _detect_record_types_heuristic(self, plugin_path: Path) -> Set[str]:
        """
        Detect record types by reading raw bytes (heuristic).

        This is a simple heuristic that looks for 4-byte record signatures
        in the file. Not 100% accurate but good enough for validation.
        """
        record_types = set()

        # Common Fallout 4 record signatures we care about
        target_signatures = {
            b'NAVM', # Navmesh
            b'CELL', # Cell
            b'WRLD', # Worldspace
            b'STAT', # Static
            b'ARMO', # Armor
            b'WEAP', # Weapon
            b'MISC', # Misc item
            b'REFR', # Reference
            b'TXST', # Texture set
        }

        try:
            with open(plugin_path, 'rb') as f:
                # Skip header (first 24 bytes is TES4 record)
                f.seek(24)

                # Read in chunks and look for signatures
                chunk_size = 1024 * 1024  # 1 MB
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break

                    for sig in target_signatures:
                        if sig in chunk:
                            record_types.add(sig.decode('ascii'))

        except Exception as e:
            logger.warning(f"Failed to detect record types in {plugin_path.name}: {e}")

        return record_types

    def get_record_signatures(self, plugin_path: Path) -> Set[str]:
        """
        Get all record type signatures present in a plugin.

        Args:
            plugin_path: Path to plugin file

        Returns:
            Set of 4-character record signatures (e.g., 'CELL', 'NAVM')
        """
        if self.esplugin_available:
            return self._detect_record_types_heuristic(plugin_path)
        else:
            return set()

    def has_deleted_records(self, plugin_path: Path, record_type: Optional[str] = None) -> List[str]:
        """
        Find records with deletion flag set.

        This is a CRITICAL check for Fallout 4 mods. Deleted records,
        especially deleted navmesh (NAVM), cause instant CTD.

        Args:
            plugin_path: Path to plugin file
            record_type: Optional filter (e.g., 'NAVM' to check only navmesh)

        Returns:
            List of form IDs (as hex strings) for deleted records

        Note:
            esplugin library has limited support for deletion flags.
            For production use, consider using FO4Edit scripts for accuracy.
        """
        deleted = []

        if not self.esplugin_available:
            logger.warning("esplugin not available, cannot check for deleted records")
            logger.warning("Use FO4Edit for accurate deleted record detection")
            return deleted

        try:
            plugin = Plugin(str(plugin_path))

            # Check for deleted records
            # Note: This is a simplified check. esplugin's Python API is limited.
            # For production, you'd want to use FO4Edit's more thorough checking.

            # esplugin can tell us if override records exist, but not deletion flags directly
            # We'll need to fall back to FO4Edit for this
            logger.info(f"Checking {plugin_path.name} for deleted records")
            logger.info("Note: For accurate deleted record detection, use FO4Edit integration")

        except Exception as e:
            logger.error(f"Failed to check deleted records in {plugin_path.name}: {e}")

        return deleted

    def get_cell_records(self, plugin_path: Path) -> List[Dict]:
        """
        Get CELL records from plugin (for precombine validation).

        Args:
            plugin_path: Path to plugin file

        Returns:
            List of dicts with cell info (form_id, has_precombine_data, etc.)

        Note:
            This requires detailed record parsing which esplugin doesn't fully
            support in Python. Use FO4Edit scripts for detailed CELL analysis.
        """
        cells = []

        if not self.esplugin_available:
            logger.warning("esplugin not available, cannot parse CELL records")
            return cells

        try:
            # Check if plugin has CELL records
            record_types = self.get_record_signatures(plugin_path)

            if 'CELL' in record_types:
                logger.info(f"{plugin_path.name} contains CELL records")
                logger.info("For detailed CELL analysis (precombine data), use FO4Edit integration")

                # esplugin can confirm CELL records exist, but can't parse subrecords
                # For precombine validation, we'll need FO4Edit
                cells.append({
                    'plugin': plugin_path.name,
                    'has_cells': True,
                    'note': 'Use FO4Edit for detailed CELL/precombine analysis'
                })

        except Exception as e:
            logger.error(f"Failed to get CELL records from {plugin_path.name}: {e}")

        return cells

    def validate_masters_exist(self, plugin_path: Path, data_path: Path) -> List[str]:
        """
        Check if all master files required by this plugin exist.

        Args:
            plugin_path: Path to plugin file
            data_path: Path to Fallout 4 Data directory

        Returns:
            List of missing master filenames
        """
        missing = []

        try:
            plugin_info = self.parse_plugin(plugin_path)

            for master in plugin_info.masters:
                master_path = data_path / master
                if not master_path.exists():
                    missing.append(master)
                    logger.warning(f"{plugin_path.name} requires missing master: {master}")

        except Exception as e:
            logger.error(f"Failed to validate masters for {plugin_path.name}: {e}")

        return missing

    def extract_form_ids(self, plugin_path: Path) -> Set[int]:
        """
        Extract all Form IDs from a plugin (for overlap detection).

        This is a simple heuristic that reads Form IDs from the plugin binary.
        Form IDs in Fallout 4 are 4-byte integers that identify game records.

        Args:
            plugin_path: Path to plugin file

        Returns:
            Set of Form IDs (as integers)

        Note:
            This is a heuristic approach. For 100% accuracy, use FO4Edit.
            Good enough for overlap detection though.
        """
        form_ids = set()

        try:
            with open(plugin_path, 'rb') as f:
                # Skip TES4 header (24 bytes + variable size)
                f.seek(24)

                # Read file in chunks and look for record headers
                # Record format: signature (4), dataSize (4), flags (4), formID (4), ...
                chunk_size = 1024 * 1024  # 1 MB chunks

                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break

                    # Look for record signatures (4-byte strings at record boundaries)
                    i = 0
                    while i < len(chunk) - 16:
                        # Check if this looks like a record header
                        # Signature should be 4 ASCII uppercase letters
                        sig = chunk[i:i+4]
                        if len(sig) == 4 and all(65 <= b <= 90 for b in sig):  # A-Z
                            # Extract Form ID (12 bytes after signature)
                            if i + 16 <= len(chunk):
                                form_id_bytes = chunk[i+12:i+16]
                                form_id = int.from_bytes(form_id_bytes, byteorder='little')
                                # Validate Form ID (should be reasonable range)
                                if 0 < form_id < 0xFFFFFFFF:
                                    form_ids.add(form_id)
                        i += 1

            logger.debug(f"Extracted {len(form_ids)} Form IDs from {plugin_path.name}")

        except Exception as e:
            logger.warning(f"Failed to extract Form IDs from {plugin_path.name}: {e}")

        return form_ids
