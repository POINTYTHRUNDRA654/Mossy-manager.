"""
Dependency-Aware Load Order Optimizer for Fallout 4

This module builds a proper load order by:
1. Parsing plugin master dependencies
2. Building a dependency graph
3. Understanding plugin semantics (what it does)
4. Sorting with topological sort to respect all dependencies
5. Grouping by type (ESM/ESL/ESP) and purpose

This is similar to how LOOT works, but tailored for Fallout 4.
"""

import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class PluginNode:
    """Represents a plugin in the dependency graph"""

    def __init__(self, name: str, file_type: str):
        self.name = name
        self.file_type = file_type  # 'esm', 'esl', or 'esp'
        self.masters: List[str] = []  # Plugins this depends on
        self.dependents: List[str] = []  # Plugins that depend on this
        self.semantic_type: str = 'content'  # Framework, patch, content, etc.
        self.priority: int = 50  # Lower number = loads earlier

    def __repr__(self):
        return f"PluginNode({self.name}, {self.file_type}, {self.semantic_type})"


class LoadOrderOptimizer:
    """
    Build optimal Fallout 4 load order respecting dependencies and semantics

    This optimizer:
    - Parses master file requirements from plugins
    - Builds a dependency graph
    - Performs topological sort to respect dependencies
    - Groups plugins by semantic type
    - Validates for circular dependencies
    """

    # Official Fallout 4 masters (must be in this order)
    OFFICIAL_MASTERS = [
        'Fallout4.esm',
        'DLCRobot.esm',
        'DLCworkshop01.esm',
        'DLCCoast.esm',
        'DLCworkshop02.esm',
        'DLCworkshop03.esm',
        'DLCNukaWorld.esm',
    ]

    # Hardcoded positions for official plugins (LOOT-style)
    # These plugins MUST be at specific indices for game stability
    HARDCODED_POSITIONS = {
        'Fallout4.esm': 0,
        'DLCRobot.esm': 1,
        'DLCworkshop01.esm': 2,
        'DLCCoast.esm': 3,
        'DLCworkshop02.esm': 4,
        'DLCworkshop03.esm': 5,
        'DLCNukaWorld.esm': 6,
        # Creation Club and official plugins
        'ccBGSFO4001-PipBoy(Black).esl': 7,
        'ccBGSFO4002-PipBoy(Blue).esl': 8,
        'ccBGSFO4003-PipBoy(Camo01).esl': 9,
        'ccBGSFO4004-PipBoy(Camo02).esl': 10,
        'ccBGSFO4006-PipBoy(Chrome).esl': 11,
        'ccBGSFO4012-PipBoy(Red).esl': 12,
        'ccBGSFO4014-PipBoy(White).esl': 13,
    }

    # Semantic patterns for plugin categorization
    # NOTE: Order matters! More specific patterns should come first.
    SEMANTIC_PATTERNS = {
        'framework': {
            'patterns': ['f4se', 'mcm', 'framework', 'library', 'base', 'core', 'resource'],
            'priority': 10,
            'description': 'Frameworks and libraries that other mods depend on'
        },
        'unofficial_patch': {
            'patterns': ['unofficial', 'bugfix', 'uff', 'bug fix'],  # Removed generic 'patch' and 'fix'
            'priority': 15,
            'description': 'Bug fixes and unofficial patches'
        },
        'overhaul': {
            'patterns': ['overhaul', 'redux', 'revamp', 'rebalance', 'overwrite'],
            'priority': 20,
            'description': 'Major gameplay or system overhauls'
        },
        'expansion': {
            'patterns': ['expansion', 'new world', 'new land', 'new area'],
            'priority': 30,
            'description': 'New worldspaces and major quest mods'
        },
        'content': {
            'patterns': ['weapon', 'armor', 'settlement', 'npc', 'enemy', 'item'],
            'priority': 40,
            'description': 'Content additions (weapons, armor, etc.)'
        },
        'visual': {
            'patterns': ['visual', 'texture', 'enb', 'lighting', 'weather', 'retexture'],
            'priority': 50,
            'description': 'Visual and graphical improvements'
        },
        'gameplay': {
            'patterns': ['gameplay', 'mechanics', 'survival', 'damage', 'ai'],
            'priority': 60,
            'description': 'Gameplay mechanic changes'
        },
        'ui': {
            'patterns': ['ui', 'hud', 'interface', 'menu', 'def_ui'],
            'priority': 70,
            'description': 'User interface modifications'
        },
        'compatibility_patch': {
            'patterns': ['compat', 'compatibility', 'merged', 'combined patch'],
            'priority': 80,
            'description': 'Compatibility patches between mods'
        },
        'conflict_resolution': {
            'patterns': ['bashed patch', 'smashed patch', 'conflict resolution', 'cr patch'],
            'priority': 90,
            'description': 'Conflict resolution patches (must load last)'
        }
    }

    def __init__(self, data_path: Optional[Path] = None, current_order: Optional[List[str]] = None):
        """
        Initialize optimizer

        Args:
            data_path: Path to Fallout 4 Data directory (for reading plugin files)
            current_order: Current load order for tie-breaking (preserves existing order when possible)
        """
        self.data_path = data_path
        self.current_order = current_order or []
        self.current_positions = {plugin: idx for idx, plugin in enumerate(self.current_order)}
        self.graph: Dict[str, PluginNode] = {}
        self.overlap_edges: Dict[str, Set[str]] = {}  # plugin -> set of plugins it conflicts with

    def analyze_plugin_semantic(self, plugin_name: str) -> Tuple[str, int]:
        """
        Determine what a plugin does based on its name

        Args:
            plugin_name: Name of the plugin

        Returns:
            Tuple of (semantic_type, priority)
        """
        plugin_lower = plugin_name.lower()

        # Check each semantic category
        for semantic_type, info in self.SEMANTIC_PATTERNS.items():
            for pattern in info['patterns']:
                if pattern in plugin_lower:
                    return semantic_type, info['priority']

        # Default to content
        return 'content', 40

    def build_graph(self, plugins: List[str], plugin_masters: Dict[str, List[str]]) -> None:
        """
        Build dependency graph from plugin list and their masters

        Args:
            plugins: List of all plugin names
            plugin_masters: Dict mapping plugin name to list of master files it requires
        """
        self.graph.clear()

        # Create nodes for all plugins
        for plugin in plugins:
            plugin_lower = plugin.lower()

            # Determine file type
            if plugin_lower.endswith('.esm'):
                file_type = 'esm'
            elif plugin_lower.endswith('.esl'):
                file_type = 'esl'
            else:
                file_type = 'esp'

            node = PluginNode(plugin, file_type)

            # Get semantic type and priority
            semantic_type, priority = self.analyze_plugin_semantic(plugin)
            node.semantic_type = semantic_type
            node.priority = priority

            # Get master dependencies
            if plugin in plugin_masters:
                node.masters = plugin_masters[plugin]

            self.graph[plugin] = node

        # Build dependency relationships
        for plugin_name, node in self.graph.items():
            for master in node.masters:
                if master in self.graph:
                    self.graph[master].dependents.append(plugin_name)

        logger.info(f"Built dependency graph with {len(self.graph)} plugins")

    def detect_overlap(self) -> None:
        """
        Detect record-level conflicts between plugins (LOOT overlap detection)

        Plugins that modify the same records have an "overlap" relationship.
        The plugin with fewer modifications should load before the one with more,
        so the more comprehensive mod wins conflicts.

        This requires parsing plugins to compare Form IDs.
        """
        if not self.data_path or not self.data_path.exists():
            logger.debug("Cannot detect overlap: data_path not available")
            return

        try:
            from mossy_manager.external.plugin_parser import PluginParser
            parser = PluginParser()

            # Build map of plugin -> set of Form IDs it modifies
            plugin_records: Dict[str, Set[int]] = {}

            for plugin_name in self.graph:
                plugin_path = self.data_path / plugin_name
                if not plugin_path.exists():
                    continue

                try:
                    info = parser.parse_plugin(plugin_path)
                    # Get all Form IDs from plugin (records it adds or modifies)
                    plugin_records[plugin_name] = set(info.form_ids) if hasattr(info, 'form_ids') else set()
                except Exception as e:
                    logger.debug(f"Could not parse {plugin_name} for overlap detection: {e}")
                    continue

            # Compare all plugin pairs for overlap
            plugins = list(self.graph.keys())
            for i, plugin_a in enumerate(plugins):
                if plugin_a not in plugin_records:
                    continue

                for plugin_b in plugins[i + 1:]:
                    if plugin_b not in plugin_records:
                        continue

                    # Check for overlapping Form IDs
                    overlap = plugin_records[plugin_a] & plugin_records[plugin_b]
                    if len(overlap) >= 5:  # Threshold: at least 5 shared records
                        # Plugin with fewer records should load first
                        if len(plugin_records[plugin_a]) < len(plugin_records[plugin_b]):
                            # A loads before B
                            if plugin_a not in self.overlap_edges:
                                self.overlap_edges[plugin_a] = set()
                            self.overlap_edges[plugin_a].add(plugin_b)
                        else:
                            # B loads before A
                            if plugin_b not in self.overlap_edges:
                                self.overlap_edges[plugin_b] = set()
                            self.overlap_edges[plugin_b].add(plugin_a)

                        logger.debug(f"Detected overlap: {plugin_a} <-> {plugin_b} ({len(overlap)} shared records)")

            if self.overlap_edges:
                logger.info(f"Detected {len(self.overlap_edges)} overlap relationships")

        except ImportError:
            logger.debug("Plugin parser not available, skipping overlap detection")
        except Exception as e:
            logger.warning(f"Error during overlap detection: {e}")

    def get_hardcoded_position(self, plugin: str) -> Optional[int]:
        """
        Get hardcoded position for official Bethesda plugins

        Args:
            plugin: Plugin name

        Returns:
            Fixed position index, or None if not hardcoded
        """
        return self.HARDCODED_POSITIONS.get(plugin)

    def detect_cycles(self) -> List[List[str]]:
        """
        Detect circular dependencies in the graph

        Returns:
            List of cycles (each cycle is a list of plugin names)
        """
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(plugin: str, path: List[str]) -> bool:
            visited.add(plugin)
            rec_stack.add(plugin)
            path.append(plugin)

            if plugin in self.graph:
                for master in self.graph[plugin].masters:
                    if master not in visited:
                        if dfs(master, path.copy()):
                            return True
                    elif master in rec_stack:
                        # Found cycle
                        cycle_start = path.index(master)
                        cycles.append(path[cycle_start:])
                        return True

            rec_stack.remove(plugin)
            return False

        for plugin in self.graph:
            if plugin not in visited:
                dfs(plugin, [])

        return cycles

    def topological_sort(self) -> List[str]:
        """
        Perform topological sort respecting dependencies, hardcoded positions, and overlap

        Edge Priority (LOOT-style):
        1. Hardcoded positions (Bethesda official plugins)
        2. Master dependencies (if B requires A as master, A loads first)
        3. Overlap relationships (fewer modifications loads first)
        4. Semantic priority (frameworks before content, patches last)
        5. Tie-break with existing order (preserve user preferences)

        Returns:
            Sorted list of plugin names
        """
        # Separate hardcoded plugins from others
        hardcoded_plugins = {}
        regular_plugins = []

        for plugin in self.graph:
            pos = self.get_hardcoded_position(plugin)
            if pos is not None:
                hardcoded_plugins[pos] = plugin
            else:
                regular_plugins.append(plugin)

        # Build in-degree map for regular plugins (number of dependencies each has)
        in_degree = {}
        for plugin in regular_plugins:
            # Count master dependencies (including hardcoded plugins as masters)
            degree = 0
            for master in self.graph[plugin].masters:
                # Count dependency if master exists in graph (hardcoded or regular)
                if master in self.graph:
                    degree += 1

            # Add overlap relationships (plugins that must load before this one)
            for other_plugin, targets in self.overlap_edges.items():
                if plugin in targets and other_plugin in regular_plugins:
                    degree += 1

            in_degree[plugin] = degree

        # Reduce in_degree for plugins that depend on hardcoded plugins
        # (since hardcoded plugins are already placed and won't be processed in the loop)
        for hardcoded_plugin in hardcoded_plugins.values():
            if hardcoded_plugin in self.graph:
                for dependent in self.graph[hardcoded_plugin].dependents:
                    if dependent in in_degree:
                        in_degree[dependent] -= 1

        # Queue of plugins with no dependencies
        queue = deque()
        for plugin, degree in in_degree.items():
            if degree == 0:
                queue.append(plugin)

        result = []

        while queue:
            # Sort queue by priority before processing (LOOT edge priority order)
            queue = deque(sorted(queue, key=lambda p: (
                # 1. Semantic priority (lower = loads earlier)
                self.graph[p].priority,
                # 2. File type (ESM < ESL < ESP)
                {'esm': 0, 'esl': 1, 'esp': 2}[self.graph[p].file_type],
                # 3. Tie-break with current position (preserve existing order when possible)
                self.current_positions.get(p, 999999),
                # 4. Alphabetical (final tie-break)
                p.lower()
            )))

            plugin = queue.popleft()
            result.append(plugin)

            # Reduce in-degree for dependent plugins
            for dependent in self.graph[plugin].dependents:
                if dependent in in_degree:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

            # Reduce in-degree for overlap relationships
            if plugin in self.overlap_edges:
                for target in self.overlap_edges[plugin]:
                    if target in in_degree:
                        in_degree[target] -= 1
                        if in_degree[target] == 0:
                            queue.append(target)

        # Check if all plugins were sorted (no cycles)
        if len(result) != len(regular_plugins):
            unsorted = set(regular_plugins) - set(result)
            logger.error(f"Circular dependency detected! Unsorted plugins: {unsorted}")
            # Add remaining plugins to end (sorted by current position for stability)
            remaining = sorted(unsorted, key=lambda p: self.current_positions.get(p, 999999))
            result.extend(remaining)

        # Combine hardcoded plugins with sorted regular plugins
        final_result = []

        # Place hardcoded plugins at their fixed positions
        if hardcoded_plugins:
            max_hardcoded_pos = max(hardcoded_plugins.keys())

            # Build the final list with hardcoded plugins in place
            for i in range(max_hardcoded_pos + 1):
                if i in hardcoded_plugins:
                    final_result.append(hardcoded_plugins[i])
                else:
                    # Fill gaps with None temporarily
                    final_result.append(None)

            # Remove None placeholders (gaps in hardcoded positions)
            final_result = [p for p in final_result if p is not None]

        # Add all regular plugins after hardcoded ones
        final_result.extend(result)

        return final_result

    def optimize(self, plugins: List[str], plugin_masters: Dict[str, List[str]]) -> List[str]:
        """
        Optimize load order for Fallout 4 mods

        This is the main entry point. It:
        1. Builds dependency graph
        2. Detects circular dependencies
        3. Detects overlap (record-level conflicts)
        4. Performs topological sort with LOOT-style edge priorities
        5. Ensures hardcoded positions for official plugins
        6. Uses tie-breaking to preserve existing order
        7. Returns optimal load order

        Args:
            plugins: List of plugin names
            plugin_masters: Dict mapping plugin name to its master file requirements

        Returns:
            Optimized list of plugin names
        """
        logger.info(f"Optimizing load order for {len(plugins)} plugins")

        # Build dependency graph
        self.build_graph(plugins, plugin_masters)

        # Check for circular dependencies
        cycles = self.detect_cycles()
        if cycles:
            logger.warning(f"Found {len(cycles)} circular dependencies:")
            for cycle in cycles:
                logger.warning(f"  Cycle: {' -> '.join(cycle)}")

        # Detect overlap (record-level conflicts)
        logger.info("Detecting record-level conflicts...")
        self.detect_overlap()

        # Perform topological sort
        sorted_plugins = self.topological_sort()

        # Log statistics
        hardcoded_count = sum(1 for p in sorted_plugins if self.get_hardcoded_position(p) is not None)
        logger.info(
            f"Optimized load order: "
            f"{hardcoded_count} hardcoded positions, "
            f"{sum(1 for p in sorted_plugins if self.graph[p].file_type == 'esm')} ESMs, "
            f"{sum(1 for p in sorted_plugins if self.graph[p].file_type == 'esl')} ESLs, "
            f"{sum(1 for p in sorted_plugins if self.graph[p].file_type == 'esp')} ESPs"
        )

        return sorted_plugins

    def explain_order(self, plugin_name: str) -> str:
        """
        Explain why a plugin is in its position

        Args:
            plugin_name: Name of the plugin

        Returns:
            Human-readable explanation
        """
        if plugin_name not in self.graph:
            return f"{plugin_name} not found in graph"

        node = self.graph[plugin_name]

        explanation = f"{plugin_name}:\n"
        explanation += f"  Type: {node.file_type.upper()}\n"
        explanation += f"  Category: {node.semantic_type}\n"
        explanation += f"  Priority: {node.priority}\n"

        if node.masters:
            explanation += f"  Depends on: {', '.join(node.masters)}\n"

        if node.dependents:
            explanation += f"  Required by: {', '.join(node.dependents)}\n"

        return explanation
