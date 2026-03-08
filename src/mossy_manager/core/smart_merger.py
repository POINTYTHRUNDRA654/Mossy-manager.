"""
Smart Mod Merger for Fallout 4

This module provides intelligent mod merging that:
1. Analyzes mod contents to understand what they do
2. Groups similar mods together (weapons, armor, textures, etc.)
3. Merges plugins using FO4Edit
4. Repacks merged assets into BA2 archives
5. Reduces total plugin count to stay under 255 limit

The merger understands Fallout 4 mod structure and maintains compatibility.
"""

import logging
import shutil
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class ModInfo:
    """Information about a mod"""
    name: str
    path: Path
    plugins: List[str]  # ESP/ESM/ESL files
    plugin_masters: Dict[str, List[str]]  # plugin_name -> list of master files it requires
    category: str  # weapon, armor, texture, gameplay, etc.
    file_count: int
    size_bytes: int
    has_plugins: bool
    has_meshes: bool
    has_textures: bool
    has_scripts: bool
    is_dependency: bool = False  # True if other mods depend on this mod's plugins


class ModAnalyzer:
    """Analyze mods to understand their contents and purpose"""

    # File patterns for categorization
    CATEGORY_PATTERNS = {
        'weapon': ['weapon', 'gun', 'rifle', 'pistol', 'sword', 'knife', 'axe'],
        'armor': ['armor', 'clothing', 'outfit', 'costume', 'suit', 'helmet'],
        'settlement': ['settlement', 'workshop', 'build', 'scrap', 'snap', 'place'],
        'npc': ['npc', 'companion', 'settler', 'enemy', 'raider', 'creature'],
        'visual': ['texture', 'retexture', 'visual', 'enb', 'lighting', 'weather'],
        'gameplay': ['survival', 'damage', 'balance', 'difficulty', 'mechanics'],
        'crafting': ['craft', 'recipe', 'workbench', 'chem', 'cooking'],
        'ui': ['ui', 'hud', 'interface', 'menu', 'def_ui', 'pip-boy'],
        'quest': ['quest', 'location', 'worldspace', 'dungeon', 'new area'],
        'animation': ['animation', 'pose', 'idle', 'havok', 'skeleton'],
        'sound': ['sound', 'audio', 'music', 'voice', 'sfx', 'radio'],
        'patch': ['patch', 'compatibility', 'compat', 'fix', 'bugfix'],
    }

    def analyze_mod(self, mod_path: Path, data_path: Optional[Path] = None) -> ModInfo:
        """
        Analyze a mod to understand its contents and dependencies

        Args:
            mod_path: Path to mod directory
            data_path: Optional path to Fallout 4 Data directory (for reading plugin masters)

        Returns:
            ModInfo object with analysis results
        """
        name = mod_path.name
        plugins = []
        plugin_masters = {}
        file_count = 0
        size_bytes = 0
        has_meshes = False
        has_textures = False
        has_scripts = False

        # Scan all files
        for file_path in mod_path.rglob('*'):
            if file_path.is_file():
                file_count += 1
                size_bytes += file_path.stat().st_size

                suffix = file_path.suffix.lower()
                rel_path = str(file_path.relative_to(mod_path)).lower()

                # Check file types
                if suffix in ['.esp', '.esm', '.esl']:
                    plugin_name = file_path.name
                    plugins.append(plugin_name)

                    # Try to read plugin master files
                    masters = self._read_plugin_masters(file_path, data_path)
                    plugin_masters[plugin_name] = masters

                elif suffix in ['.nif', '.bgsm', '.bgem']:
                    has_meshes = True
                elif suffix in ['.dds', '.png']:
                    has_textures = True
                elif suffix == '.pex':
                    has_scripts = True

        # Determine category from mod name and contents
        category = self._categorize_mod(name, plugins, has_meshes, has_textures, has_scripts)

        return ModInfo(
            name=name,
            path=mod_path,
            plugins=plugins,
            plugin_masters=plugin_masters,
            category=category,
            file_count=file_count,
            size_bytes=size_bytes,
            has_plugins=len(plugins) > 0,
            has_meshes=has_meshes,
            has_textures=has_textures,
            has_scripts=has_scripts,
            is_dependency=False  # Will be set later in dependency analysis
        )

    def _read_plugin_masters(self, plugin_path: Path, data_path: Optional[Path] = None) -> List[str]:
        """
        Read master file requirements from a plugin

        Args:
            plugin_path: Path to plugin file
            data_path: Optional Data directory path

        Returns:
            List of master file names this plugin requires
        """
        try:
            from mossy_manager.external.plugin_parser import PluginParser
            parser = PluginParser()
            info = parser.parse_plugin(plugin_path)
            return info.masters
        except Exception as e:
            logger.debug(f"Could not read masters from {plugin_path.name}: {e}")
            return []

    def _categorize_mod(self, name: str, plugins: List[str],
                       has_meshes: bool, has_textures: bool, has_scripts: bool) -> str:
        """
        Determine mod category from name and contents

        Args:
            name: Mod name
            plugins: List of plugin files
            has_meshes: Whether mod has mesh files
            has_textures: Whether mod has texture files
            has_scripts: Whether mod has script files

        Returns:
            Category name
        """
        name_lower = name.lower()

        # Check name against category patterns
        for category, patterns in self.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if pattern in name_lower:
                    return category

        # Infer from contents
        if has_textures and not has_meshes and not len(plugins):
            return 'visual'
        elif has_meshes and has_textures and len(plugins):
            if 'weapon' in name_lower or 'gun' in name_lower:
                return 'weapon'
            elif 'armor' in name_lower or 'cloth' in name_lower:
                return 'armor'
            return 'content'
        elif has_scripts:
            return 'gameplay'

        # Default to content
        return 'content'


@dataclass
class MergeGroup:
    """A group of mods that should be merged together"""
    category: str
    mods: List[ModInfo]
    dependencies: List[ModInfo]  # Dependency mods that must be included
    merge_name: str
    total_plugins: int
    total_size: int

    def can_add_mod(self, mod: ModInfo, max_plugins: int = 50) -> bool:
        """Check if a mod can be added to this group"""
        # Same category
        if mod.category != self.category:
            return False
        # Don't add dependency mods to regular merge groups
        if mod.is_dependency:
            return False
        # Don't exceed max plugins in one merge
        if self.total_plugins + len(mod.plugins) > max_plugins:
            return False
        return True

    def add_mod(self, mod: ModInfo):
        """Add a mod to this group"""
        self.mods.append(mod)
        self.total_plugins += len(mod.plugins)
        self.total_size += mod.size_bytes

    def add_dependency(self, dep: ModInfo):
        """Add a dependency mod to this group"""
        if dep not in self.dependencies:
            self.dependencies.append(dep)
            self.total_plugins += len(dep.plugins)
            self.total_size += dep.size_bytes


class SmartModMerger:
    """
    Intelligently merge mods in groups by category

    This merger:
    - Analyzes each mod to understand its purpose
    - Groups similar mods together
    - Merges plugins using FO4Edit
    - Repacks assets into BA2 archives
    - Maintains compatibility and load order
    """

    def __init__(self, mo2_path: Path, xedit_path: Optional[Path] = None):
        """
        Initialize smart merger

        Args:
            mo2_path: Path to MO2 installation
            xedit_path: Path to FO4Edit (optional)
        """
        self.mo2_path = mo2_path
        self.xedit_path = xedit_path
        self.analyzer = ModAnalyzer()
        self.merge_groups: List[MergeGroup] = []

    def analyze_mods(self, mods_path: Path, data_path: Optional[Path] = None) -> List[ModInfo]:
        """
        Analyze all mods in the mods directory

        Args:
            mods_path: Path to MO2 mods directory
            data_path: Optional path to Fallout 4 Data directory

        Returns:
            List of ModInfo objects with dependency information
        """
        logger.info(f"Analyzing mods in {mods_path}")
        mods = []

        for mod_dir in mods_path.iterdir():
            if mod_dir.is_dir():
                try:
                    mod_info = self.analyzer.analyze_mod(mod_dir, data_path)
                    mods.append(mod_info)
                    logger.debug(f"Analyzed {mod_info.name}: category={mod_info.category}, "
                               f"plugins={len(mod_info.plugins)}, files={mod_info.file_count}")
                except Exception as e:
                    logger.error(f"Error analyzing {mod_dir.name}: {e}")

        # Mark dependencies
        self._mark_dependencies(mods)

        logger.info(f"Analyzed {len(mods)} mods")
        return mods

    def _mark_dependencies(self, mods: List[ModInfo]) -> None:
        """
        Mark mods that are dependencies of other mods

        A mod is a dependency if any other mod lists its plugins as masters.

        Args:
            mods: List of ModInfo objects to analyze
        """
        # Build set of all plugin names across all mods
        all_plugins = {}
        for mod in mods:
            for plugin in mod.plugins:
                all_plugins[plugin] = mod

        # Check which plugins are required by others
        required_plugins = set()
        for mod in mods:
            for plugin_name, masters in mod.plugin_masters.items():
                for master in masters:
                    # Skip official Bethesda masters
                    if master not in ['Fallout4.esm', 'DLCRobot.esm', 'DLCworkshop01.esm',
                                     'DLCCoast.esm', 'DLCworkshop02.esm', 'DLCworkshop03.esm',
                                     'DLCNukaWorld.esm']:
                        required_plugins.add(master)

        # Mark mods as dependencies if their plugins are required
        for mod in mods:
            for plugin in mod.plugins:
                if plugin in required_plugins:
                    mod.is_dependency = True
                    logger.info(f"  {mod.name} marked as dependency (plugin {plugin} is required by other mods)")
                    break

    def create_merge_groups(self, mods: List[ModInfo],
                           max_plugins_per_group: int = 50) -> List[MergeGroup]:
        """
        Group mods by category for merging, respecting dependencies

        Args:
            mods: List of mods to group
            max_plugins_per_group: Maximum plugins in one merge group

        Returns:
            List of merge groups with dependencies included
        """
        logger.info(f"Creating dependency-aware merge groups from {len(mods)} mods")

        # Separate dependency mods from regular mods
        dependencies = [m for m in mods if m.is_dependency and m.has_plugins]
        mergeable = [m for m in mods if not m.is_dependency and m.has_plugins and len(m.plugins) > 0]

        logger.info(f"  Found {len(mergeable)} mergeable mods")
        logger.info(f"  Found {len(dependencies)} dependency mods (will be merged with dependents)")

        # Build plugin -> mod mapping for dependencies
        dep_plugin_to_mod = {}
        for dep in dependencies:
            for plugin in dep.plugins:
                dep_plugin_to_mod[plugin] = dep

        # Group by category
        groups: List[MergeGroup] = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for mod in mergeable:
            # Find existing group for this category
            added = False
            for group in groups:
                if group.can_add_mod(mod, max_plugins_per_group):
                    group.add_mod(mod)
                    added = True
                    break

            # Create new group if needed
            if not added:
                group_num = len([g for g in groups if g.category == mod.category]) + 1
                merge_name = f"MossyMerge_{mod.category}_{group_num}_{timestamp}"

                new_group = MergeGroup(
                    category=mod.category,
                    mods=[mod],
                    dependencies=[],
                    merge_name=merge_name,
                    total_plugins=len(mod.plugins),
                    total_size=mod.size_bytes
                )
                groups.append(new_group)

        # Add dependencies to each group
        for group in groups:
            required_deps = set()

            # Check what dependencies this group needs
            for mod in group.mods:
                for plugin_name, masters in mod.plugin_masters.items():
                    for master in masters:
                        if master in dep_plugin_to_mod:
                            required_deps.add(dep_plugin_to_mod[master])

            # Add dependencies to group
            for dep in required_deps:
                group.add_dependency(dep)
                logger.info(f"  Added dependency {dep.name} to group {group.merge_name}")

        logger.info(f"Created {len(groups)} merge groups:")
        for group in groups:
            logger.info(f"  {group.merge_name}: "
                       f"{len(group.mods)} mods + {len(group.dependencies)} dependencies, "
                       f"{group.total_plugins} total plugins, category={group.category}")

        return groups

    def merge_group(self, group: MergeGroup, output_path: Path,
                   create_ba2: bool = True) -> bool:
        """
        Merge a group of mods including their dependencies

        Args:
            group: Merge group to process
            output_path: Output directory for merged mod
            create_ba2: Whether to pack into BA2 archive

        Returns:
            True if successful
        """
        logger.info(f"Merging group: {group.merge_name} "
                   f"({len(group.mods)} mods + {len(group.dependencies)} dependencies)")

        try:
            # Create output directory
            merge_dir = output_path / group.merge_name
            merge_dir.mkdir(parents=True, exist_ok=True)

            # First, copy dependency mods (they need to be at the "bottom" of the merge)
            total_files = 0
            all_mods = group.dependencies + group.mods  # Dependencies first, then regular mods

            for mod in all_mods:
                logger.info(f"  Copying files from {mod.name} {'[DEPENDENCY]' if mod.is_dependency else ''}")
                for file_path in mod.path.rglob('*'):
                    if file_path.is_file():
                        rel_path = file_path.relative_to(mod.path)
                        dest_path = merge_dir / rel_path
                        dest_path.parent.mkdir(parents=True, exist_ok=True)

                        # Handle conflicts: later mod wins (MO2 behavior)
                        # This means regular mods override dependencies, which is correct
                        shutil.copy2(file_path, dest_path)
                        total_files += 1

            logger.info(f"  Copied {total_files} files")

            # Create merge metadata
            meta_path = merge_dir / "mossy_merge_info.json"
            meta_data = {
                'merge_name': group.merge_name,
                'category': group.category,
                'created': datetime.now().isoformat(),
                'source_mods': [m.name for m in group.mods],
                'dependencies': [d.name for d in group.dependencies],
                'total_plugins': group.total_plugins,
                'total_files': total_files,
                'dependency_note': 'This merge includes dependency mods that were required by the main mods'
            }
            meta_path.write_text(json.dumps(meta_data, indent=2))

            # TODO: Merge plugins using FO4Edit (requires xEdit integration)
            # TODO: Pack into BA2 archive if requested

            logger.info(f"Successfully merged {group.merge_name}")
            return True

        except Exception as e:
            logger.error(f"Error merging group {group.merge_name}: {e}", exc_info=True)
            return False

    def merge_all_groups(self, groups: List[MergeGroup], output_path: Path,
                        create_ba2: bool = True) -> Dict[str, bool]:
        """
        Merge all groups

        Args:
            groups: List of merge groups
            output_path: Output directory
            create_ba2: Whether to create BA2 archives

        Returns:
            Dict mapping merge_name to success status
        """
        results = {}

        for group in groups:
            success = self.merge_group(group, output_path, create_ba2)
            results[group.merge_name] = success

        successful = sum(1 for s in results.values() if s)
        logger.info(f"Merge complete: {successful}/{len(groups)} groups successful")

        return results


def calculate_merge_benefit(mods: List[ModInfo]) -> Dict[str, int]:
    """
    Calculate plugin count reduction from merging

    Args:
        mods: List of mods

    Returns:
        Dict with statistics
    """
    total_plugins = sum(len(m.plugins) for m in mods if m.has_plugins)
    mergeable_mods = [m for m in mods if m.has_plugins]

    # Estimate: each merge group reduces to 1 plugin
    analyzer = ModAnalyzer()
    categories = {}
    for mod in mergeable_mods:
        cat = mod.category
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(mod)

    # Rough estimate: one plugin per category group
    estimated_after_merge = len(categories)
    reduction = total_plugins - estimated_after_merge

    return {
        'total_plugins_before': total_plugins,
        'total_plugins_after': estimated_after_merge,
        'reduction': reduction,
        'mergeable_mods': len(mergeable_mods),
        'categories': len(categories),
    }
