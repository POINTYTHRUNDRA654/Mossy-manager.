"""
BA2 Archive Handler for Fallout 4

This module provides Python interface to BSArch (bsarch.exe) for creating
and managing BA2 archive files.

BA2 archives are Bethesda's archive format used in Fallout 4 for packaging
textures, meshes, sounds, and other game assets.

Benefits of BA2 archives:
- Reduces file count (important for performance)
- Compresses assets (saves disk space)
- Improves load times
- Required for certain mod distributions
"""

import logging
import subprocess
from pathlib import Path
from typing import List, Optional, Dict
from enum import Enum

logger = logging.getLogger(__name__)


class BA2Type(Enum):
    """BA2 archive types"""
    GENERAL = "General"  # Meshes, scripts, misc files
    TEXTURES = "Textures"  # DDS texture files


class BSArchIntegration:
    """
    Interface to BSArch.exe for BA2 archive operations

    BSArch is the standard tool for creating/extracting BA2 archives.
    Download from: https://www.nexusmods.com/fallout4/mods/12876
    """

    def __init__(self, bsarch_path: Optional[Path] = None):
        """
        Initialize BSArch integration

        Args:
            bsarch_path: Path to bsarch.exe (if None, searches common locations)
        """
        self.bsarch_path = bsarch_path or self._find_bsarch()

    def _find_bsarch(self) -> Optional[Path]:
        """
        Find bsarch.exe in common locations

        Returns:
            Path to bsarch.exe or None
        """
        # Common locations
        search_paths = [
            Path.cwd() / "bsarch.exe",
            Path.cwd() / "tools" / "bsarch.exe",
            Path.home() / "Documents" / "Tools" / "bsarch.exe",
            Path("C:/Tools/bsarch.exe"),
        ]

        for path in search_paths:
            if path.exists():
                logger.info(f"Found bsarch at: {path}")
                return path

        logger.warning("bsarch.exe not found in common locations")
        return None

    def is_available(self) -> bool:
        """Check if bsarch is available"""
        return self.bsarch_path is not None and self.bsarch_path.exists()

    def pack_directory(self, input_dir: Path, output_ba2: Path,
                      archive_type: BA2Type = BA2Type.GENERAL,
                      compress: bool = True) -> bool:
        """
        Pack a directory into a BA2 archive

        Args:
            input_dir: Directory containing files to pack
            output_ba2: Output BA2 file path
            archive_type: Type of archive (General or Textures)
            compress: Whether to compress files

        Returns:
            True if successful
        """
        if not self.is_available():
            logger.error("bsarch.exe not available")
            return False

        if not input_dir.exists():
            logger.error(f"Input directory not found: {input_dir}")
            return False

        logger.info(f"Packing {input_dir} into {output_ba2}")

        try:
            # BSArch command format:
            # bsarch pack <folder> <archive.ba2> -fo4 [-general|-textures] [-z]
            args = [
                str(self.bsarch_path),
                "pack",
                str(input_dir),
                str(output_ba2),
                "-fo4",  # Fallout 4 format
            ]

            # Archive type
            if archive_type == BA2Type.TEXTURES:
                args.append("-textures")
            else:
                args.append("-general")

            # Compression
            if compress:
                args.append("-z")

            # Run bsarch
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                logger.info(f"Successfully created {output_ba2}")
                logger.debug(f"BSArch output: {result.stdout}")
                return True
            else:
                logger.error(f"BSArch failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("BSArch timed out after 5 minutes")
            return False
        except Exception as e:
            logger.error(f"Error running BSArch: {e}", exc_info=True)
            return False

    def extract_archive(self, ba2_path: Path, output_dir: Path) -> bool:
        """
        Extract a BA2 archive

        Args:
            ba2_path: Path to BA2 file
            output_dir: Output directory

        Returns:
            True if successful
        """
        if not self.is_available():
            logger.error("bsarch.exe not available")
            return False

        if not ba2_path.exists():
            logger.error(f"BA2 file not found: {ba2_path}")
            return False

        logger.info(f"Extracting {ba2_path} to {output_dir}")

        try:
            # BSArch command: bsarch unpack <archive.ba2> <folder>
            args = [
                str(self.bsarch_path),
                "unpack",
                str(ba2_path),
                str(output_dir),
            ]

            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                logger.info(f"Successfully extracted to {output_dir}")
                return True
            else:
                logger.error(f"BSArch extraction failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error extracting BA2: {e}", exc_info=True)
            return False

    def list_contents(self, ba2_path: Path) -> Optional[List[str]]:
        """
        List files in a BA2 archive

        Args:
            ba2_path: Path to BA2 file

        Returns:
            List of file paths in archive, or None on error
        """
        if not self.is_available():
            logger.error("bsarch.exe not available")
            return None

        if not ba2_path.exists():
            logger.error(f"BA2 file not found: {ba2_path}")
            return None

        try:
            # BSArch command: bsarch list <archive.ba2>
            args = [
                str(self.bsarch_path),
                "list",
                str(ba2_path),
            ]

            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                # Parse output
                files = []
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if line and not line.startswith('['):  # Skip header lines
                        files.append(line)
                return files
            else:
                logger.error(f"BSArch list failed: {result.stderr}")
                return None

        except Exception as e:
            logger.error(f"Error listing BA2 contents: {e}", exc_info=True)
            return None


def pack_merged_mod(mod_path: Path, output_dir: Path,
                   bsarch_path: Optional[Path] = None) -> Dict[str, Path]:
    """
    Pack a merged mod into BA2 archives

    This function:
    1. Separates textures from other files
    2. Creates <ModName> - Textures.ba2 for textures
    3. Creates <ModName> - Main.ba2 for other files
    4. Leaves plugins (.esp/.esm/.esl) loose (required by game)

    Args:
        mod_path: Path to merged mod directory
        output_dir: Output directory for BA2 files
        bsarch_path: Optional path to bsarch.exe

    Returns:
        Dict mapping archive type to created BA2 path
    """
    logger.info(f"Packing merged mod: {mod_path.name}")

    bsarch = BSArchIntegration(bsarch_path)
    if not bsarch.is_available():
        logger.error("Cannot pack BA2: bsarch not available")
        return {}

    mod_name = mod_path.name
    results = {}

    # Create temporary directories for packing
    temp_textures = mod_path.parent / f"{mod_name}_temp_textures"
    temp_main = mod_path.parent / f"{mod_name}_temp_main"

    try:
        temp_textures.mkdir(exist_ok=True)
        temp_main.mkdir(exist_ok=True)

        # Separate files by type
        for file_path in mod_path.rglob('*'):
            if not file_path.is_file():
                continue

            rel_path = file_path.relative_to(mod_path)
            suffix = file_path.suffix.lower()

            # Skip plugins (must stay loose)
            if suffix in ['.esp', '.esm', '.esl', '.json']:
                continue

            # Textures go to texture archive
            if suffix == '.dds':
                dest = temp_textures / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(file_path, dest)
            # Everything else goes to main archive
            else:
                dest = temp_main / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(file_path, dest)

        # Pack textures archive
        if list(temp_textures.rglob('*.dds')):
            textures_ba2 = output_dir / f"{mod_name} - Textures.ba2"
            if bsarch.pack_directory(temp_textures, textures_ba2, BA2Type.TEXTURES):
                results['textures'] = textures_ba2
                logger.info(f"Created texture archive: {textures_ba2.name}")

        # Pack main archive
        if list(temp_main.rglob('*')):
            main_ba2 = output_dir / f"{mod_name} - Main.ba2"
            if bsarch.pack_directory(temp_main, main_ba2, BA2Type.GENERAL):
                results['main'] = main_ba2
                logger.info(f"Created main archive: {main_ba2.name}")

    finally:
        # Cleanup temp directories
        import shutil
        if temp_textures.exists():
            shutil.rmtree(temp_textures, ignore_errors=True)
        if temp_main.exists():
            shutil.rmtree(temp_main, ignore_errors=True)

    logger.info(f"Packed {len(results)} BA2 archives")
    return results
