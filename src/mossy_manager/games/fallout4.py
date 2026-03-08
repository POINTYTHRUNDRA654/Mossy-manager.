"""
Fallout 4 Specific Load Order Rules and Knowledge

This module contains comprehensive Fallout 4 modding knowledge including:
- Official DLC load order
- Plugin categories and groups
- Common conflict patterns
- Load order rules and best practices
"""

import logging
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class Fallout4Rules:
    """
    Comprehensive Fallout 4 load order rules and modding knowledge
    
    This class implements advanced knowledge of Fallout 4 modding including:
    - Master file dependencies and ordering
    - DLC load order requirements
    - Plugin categories (UI, weapons, armor, settlements, etc.)
    - Common conflict patterns
    - Best practices for stable load orders
    """
    
    # Official Fallout 4 master files and DLC in required order
    MASTER_FILES = [
        'Fallout4.esm',
        'DLCRobot.esm',          # Automatron
        'DLCworkshop01.esm',     # Wasteland Workshop
        'DLCCoast.esm',          # Far Harbor
        'DLCworkshop02.esm',     # Contraptions Workshop
        'DLCworkshop03.esm',     # Vault-Tec Workshop
        'DLCNukaWorld.esm',      # Nuka-World
    ]
    
    # High priority mods that should load early
    HIGH_PRIORITY_PATTERNS = [
        'unofficial',  # Unofficial Fallout 4 Patch
        'f4se',        # Fallout 4 Script Extender plugins
        'xse',         # Script extender related
        'mcm',         # Mod Configuration Menu
        'achievement', # Achievement mods
    ]
    
    # Plugin categories with load order preferences
    PLUGIN_CATEGORIES = {
        'core_fixes': {
            'priority': 10,
            'patterns': ['patch', 'fix', 'unofficial', 'bugfix'],
            'description': 'Core fixes and patches'
        },
        'framework': {
            'priority': 20,
            'patterns': ['framework', 'f4se', 'mcm', 'library', 'resource'],
            'description': 'Frameworks and libraries'
        },
        'overhauls': {
            'priority': 30,
            'patterns': ['overhaul', 'rebalance', 'redux', 'revamp'],
            'description': 'Major overhauls'
        },
        'gameplay': {
            'priority': 40,
            'patterns': ['gameplay', 'mechanic', 'survival', 'difficulty'],
            'description': 'Gameplay changes'
        },
        'settlements': {
            'priority': 50,
            'patterns': ['settlement', 'workshop', 'build', 'sim settlements'],
            'description': 'Settlement and building mods'
        },
        'weapons': {
            'priority': 60,
            'patterns': ['weapon', 'gun', 'rifle', 'pistol', 'melee'],
            'description': 'Weapon additions and changes'
        },
        'armor': {
            'priority': 70,
            'patterns': ['armor', 'clothing', 'outfit', 'costume'],
            'description': 'Armor and clothing mods'
        },
        'npc': {
            'priority': 80,
            'patterns': ['npc', 'companion', 'settler', 'enemy'],
            'description': 'NPC and companion mods'
        },
        'world': {
            'priority': 90,
            'patterns': ['world', 'location', 'quest', 'dungeon'],
            'description': 'World additions and quests'
        },
        'visual': {
            'priority': 100,
            'patterns': ['texture', 'visual', 'enb', 'lighting', 'weather'],
            'description': 'Visual and graphics mods'
        },
        'audio': {
            'priority': 110,
            'patterns': ['sound', 'audio', 'music', 'radio'],
            'description': 'Audio mods'
        },
        'ui': {
            'priority': 120,
            'patterns': ['ui', 'hud', 'interface', 'menu', 'pip-boy'],
            'description': 'User interface mods'
        },
        'patches': {
            'priority': 130,
            'patterns': ['compat', 'compatibility', 'patch'],
            'description': 'Compatibility patches'
        }
    }
    
    # Known conflict groups - plugins that commonly conflict
    CONFLICT_GROUPS = {
        'settlement_overhauls': [
            'sim settlements', 'workshop', 'settlement', 'scrap'
        ],
        'weapon_overhauls': [
            'modern firearms', 'weapons of fate', 'arbitration'
        ],
        'lighting_mods': [
            'enb', 'lighting', 'weather', 'interiors'
        ],
        'body_mods': [
            'bodyslide', 'cbbe', 'fusion girl', 'atomic beauty'
        ]
    }
    
    # Plugins that should always load last
    LOAD_LAST_PATTERNS = [
        'bashed patch',
        'smashed patch',
        'merged patch',
        'conflict resolution',
    ]
    
    @classmethod
    def is_master_file(cls, plugin_name: str) -> bool:
        """Check if a plugin is an official master file"""
        return plugin_name in cls.MASTER_FILES
    
    @classmethod
    def get_master_file_priority(cls, plugin_name: str) -> int:
        """Get the priority order for master files"""
        try:
            return cls.MASTER_FILES.index(plugin_name)
        except ValueError:
            return 9999  # Not a master file
    
    @classmethod
    def categorize_plugin(cls, plugin_name: str) -> Tuple[str, int]:
        """
        Categorize a plugin and return category name and priority
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Tuple of (category_name, priority)
        """
        plugin_lower = plugin_name.lower()
        
        # Check for high priority patterns first
        for pattern in cls.HIGH_PRIORITY_PATTERNS:
            if pattern in plugin_lower:
                return ('high_priority', 5)
        
        # Check if it should load last
        for pattern in cls.LOAD_LAST_PATTERNS:
            if pattern in plugin_lower:
                return ('load_last', 999)
        
        # Check categories
        for category, info in cls.PLUGIN_CATEGORIES.items():
            for pattern in info['patterns']:
                if pattern in plugin_lower:
                    return (category, info['priority'])
        
        # Default category
        return ('general', 50)
    
    @classmethod
    def get_plugin_dependencies(cls, plugin_name: str) -> List[str]:
        """
        Get known dependencies for common plugins
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            List of required master files
        """
        plugin_lower = plugin_name.lower()
        
        dependencies = ['Fallout4.esm']  # All plugins depend on this
        
        # Add DLC dependencies based on common patterns
        if any(x in plugin_lower for x in ['automatron', 'robot', 'dlcrobot']):
            dependencies.append('DLCRobot.esm')
        
        if any(x in plugin_lower for x in ['far harbor', 'coast', 'dlccoast']):
            dependencies.append('DLCCoast.esm')
        
        if any(x in plugin_lower for x in ['nuka world', 'nuka-world', 'nukaworld', 'dlcnukaworld']):
            dependencies.append('DLCNukaWorld.esm')
        
        if any(x in plugin_lower for x in ['workshop', 'settlement']):
            # Workshop DLCs
            if 'contraption' in plugin_lower:
                dependencies.append('DLCworkshop02.esm')
            elif 'vault' in plugin_lower:
                dependencies.append('DLCworkshop03.esm')
            else:
                dependencies.append('DLCworkshop01.esm')
        
        return dependencies
    
    @classmethod
    def check_conflicts(cls, plugin_name: str, other_plugins: List[str]) -> List[str]:
        """
        Check for potential conflicts with other plugins
        
        Args:
            plugin_name: Plugin to check
            other_plugins: List of other plugins in load order
            
        Returns:
            List of potential conflicts
        """
        conflicts = []
        plugin_lower = plugin_name.lower()
        
        # Check conflict groups
        for group_name, group_patterns in cls.CONFLICT_GROUPS.items():
            # Check if this plugin is in the group
            plugin_in_group = any(pattern in plugin_lower for pattern in group_patterns)
            
            if plugin_in_group:
                # Check if any other plugin is also in this group
                for other in other_plugins:
                    if other == plugin_name:
                        continue
                    other_lower = other.lower()
                    if any(pattern in other_lower for pattern in group_patterns):
                        conflicts.append(f"Potential conflict with {other} (same category: {group_name})")
        
        return conflicts
    
    @classmethod
    def optimize_load_order(cls, plugins: List[str], data_path: Optional[Path] = None) -> List[str]:
        """
        Optimize load order for Fallout 4 using dependency-aware algorithm

        This method:
        1. Reads master file dependencies from each plugin
        2. Builds a dependency graph
        3. Performs topological sort to respect all dependencies
        4. Groups by semantic type (framework, content, patch, etc.)
        5. Ensures ESM/ESL/ESP separation

        This is similar to how LOOT works, respecting actual plugin relationships.

        Args:
            plugins: List of plugin names
            data_path: Path to Fallout 4 Data directory (optional, for reading plugin files)

        Returns:
            Optimized list of plugin names in correct load order
        """
        logger.info(f"Optimizing Fallout 4 load order for {len(plugins)} plugins")

        # Try to read master dependencies from actual plugin files
        plugin_masters = {}

        if data_path and data_path.exists():
            try:
                from mossy_manager.external.plugin_parser import PluginParser
                parser = PluginParser()

                for plugin in plugins:
                    plugin_path = data_path / plugin
                    if plugin_path.exists():
                        try:
                            info = parser.parse_plugin(plugin_path)
                            plugin_masters[plugin] = info.masters
                            logger.debug(f"{plugin} requires: {info.masters}")
                        except Exception as e:
                            logger.warning(f"Could not parse {plugin}: {e}")
                            plugin_masters[plugin] = []
                    else:
                        plugin_masters[plugin] = []

            except ImportError:
                logger.warning("PluginParser not available, using fallback logic")

        # If we couldn't read master files, use empty dependencies
        # (will still sort by file type and semantic analysis)
        for plugin in plugins:
            if plugin not in plugin_masters:
                plugin_masters[plugin] = []

        # Use the dependency-aware optimizer with current order for tie-breaking
        from mossy_manager.core.load_order_optimizer import LoadOrderOptimizer

        optimizer = LoadOrderOptimizer(data_path, current_order=plugins)
        optimized = optimizer.optimize(plugins, plugin_masters)

        logger.info(
            f"Optimized load order: "
            f"{sum(1 for p in optimized if p in cls.MASTER_FILES)} official masters, "
            f"{sum(1 for p in optimized if p.lower().endswith('.esm') and p not in cls.MASTER_FILES)} unofficial ESMs, "
            f"{sum(1 for p in optimized if p.lower().endswith('.esl'))} ESLs, "
            f"{sum(1 for p in optimized if p.lower().endswith('.esp'))} ESPs"
        )

        return optimized
    
    @classmethod
    def validate_load_order(cls, plugins: List[str]) -> Dict[str, List[str]]:
        """
        Validate Fallout 4 load order and return issues
        
        Args:
            plugins: List of plugins in current order
            
        Returns:
            Dictionary with 'errors' and 'warnings' keys
        """
        issues = {
            'errors': [],
            'warnings': []
        }

        # Slot accounting: masters + ESPs count toward 255 cap; ESLs (.esl) do not
        slot_plugins = [p for p in plugins if not p.lower().endswith('.esl')]
        slot_count = len(slot_plugins)
        if slot_count >= 254:
            issues['errors'].append(f"Plugin cap reached ({slot_count}/255). Convert eligible plugins to ESL or remove some mods.")
        elif slot_count >= 240:
            issues['warnings'].append(f"Approaching plugin cap ({slot_count}/255). Consider ESL-flagging small ESPs to free slots.")
        
        # Check if Fallout4.esm is first
        if plugins and plugins[0] != 'Fallout4.esm':
            issues['errors'].append("Fallout4.esm must be the first plugin")
        
        # Check master file order
        master_positions = {}
        for i, plugin in enumerate(plugins):
            if plugin in cls.MASTER_FILES:
                master_positions[plugin] = i
        
        for i, master in enumerate(cls.MASTER_FILES):
            if master in master_positions:
                expected_pos = i
                actual_pos = master_positions[master]
                
                # Check if masters before this one are in correct order
                for j, prev_master in enumerate(cls.MASTER_FILES[:i]):
                    if prev_master in master_positions:
                        if master_positions[prev_master] > actual_pos:
                            issues['errors'].append(
                                f"{master} should load after {prev_master}"
                            )
        
        # Check for regular plugins loading before masters
        last_master_pos = -1
        for i, plugin in enumerate(plugins):
            if plugin in cls.MASTER_FILES:
                last_master_pos = i
            elif plugin.lower().endswith('.esm') and last_master_pos > -1:
                if i < last_master_pos:
                    issues['warnings'].append(
                        f"Master file {plugin} loading before official masters"
                    )
        
        # Check for potential conflicts
        for i, plugin in enumerate(plugins):
            conflicts = cls.check_conflicts(plugin, plugins)
            for conflict in conflicts:
                issues['warnings'].append(f"{plugin}: {conflict}")
        
        return issues
    
    @classmethod
    def get_recommendations(cls, plugins: List[str]) -> List[str]:
        """
        Get recommendations for improving the load order
        
        Args:
            plugins: Current load order
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Check for missing unofficial patch
        has_unofficial_patch = any('unofficial' in p.lower() and 'patch' in p.lower() 
                                  for p in plugins)
        if not has_unofficial_patch:
            recommendations.append(
                "Consider installing the Unofficial Fallout 4 Patch for bug fixes"
            )

        # Plugin cap mitigation suggestions
        slot_plugins = [p for p in plugins if not p.lower().endswith('.esl')]
        slot_count = len(slot_plugins)
        if slot_count >= 240:
            recommendations.append(
                f"Plugin count is {slot_count}/255. ESL-flag smaller ESPs or merge patches to free slots."
            )
        
        # Check for F4SE-dependent mods without checking if F4SE is needed
        has_f4se_plugins = any('f4se' in p.lower() or 'mcm' in p.lower() 
                              for p in plugins)
        if has_f4se_plugins:
            recommendations.append(
                "Ensure F4SE (Fallout 4 Script Extender) is properly installed"
            )
        
        # Check for conflicting mods in same category
        for group_name, group_patterns in cls.CONFLICT_GROUPS.items():
            group_mods = [p for p in plugins 
                         if any(pattern in p.lower() for pattern in group_patterns)]
            if len(group_mods) > 1:
                recommendations.append(
                    f"Multiple {group_name} mods detected: {', '.join(group_mods[:3])}... "
                    f"Consider creating compatibility patches"
                )
        
        return recommendations
