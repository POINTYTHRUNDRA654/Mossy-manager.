"""
PluginDependencyGraph — build and query a directed dependency graph for
Fallout 4 load orders.

Every ``.esp``/``.esl``/``.esm`` plugin implicitly depends on
``Fallout4.esm``.  DLC-dependent plugins additionally require the relevant
DLC master.  xEdit exposes the exact master list for each plugin, but because
we don't parse binary ``.esp`` files here we rely on:

  1. ``Fallout4Rules.get_plugin_dependencies()`` — heuristic name matching
  2. A user-supplied dependency map (for when xEdit data is available)

Capabilities
------------
- ``build(load_order)``             — populate the graph from a load order
- ``get_missing_masters(plugins)``  — plugins whose required master is absent
- ``get_load_order_violations(plugins)`` — plugins loading *before* their masters
- ``topological_sort(plugins)``     — a valid ordering that satisfies all deps
- ``dependency_chain(plugin)``      — full chain of transitive deps for one plugin
- ``to_dict()``                     — JSON-serialisable representation

The Reasoner gains a new rule ``MissingMaster`` fed by this module.
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from mossy_manager.games.fallout4 import Fallout4Rules

logger = logging.getLogger(__name__)


class PluginDependencyGraph:
    """
    Directed graph where an edge ``A → B`` means *A depends on B*
    (i.e. B must be loaded before A).

    Parameters
    ----------
    extra_deps : dict, optional
        ``{ plugin_name: [master1, master2, …] }`` — additional dependency
        data (e.g. parsed from xEdit or a manifest file).  Merged with the
        heuristic data from ``Fallout4Rules``.
    """

    def __init__(
        self,
        extra_deps: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        # edges[A] = set of plugins that A depends on
        self._edges: Dict[str, Set[str]] = defaultdict(set)
        # reverse edges used for topological sort
        self._reverse: Dict[str, Set[str]] = defaultdict(set)
        # all known plugin names
        self._nodes: Set[str] = set()
        self._extra_deps: Dict[str, List[str]] = extra_deps or {}

    # ── Graph construction ────────────────────────────────────────────

    def add_plugin(self, plugin: str, masters: Optional[List[str]] = None) -> None:
        """
        Register a plugin and its explicit masters.

        If *masters* is omitted the heuristic from ``Fallout4Rules`` is used.
        """
        self._nodes.add(plugin)
        deps = list(masters) if masters is not None else (
            Fallout4Rules.get_plugin_dependencies(plugin)
        )
        # Merge any extra deps supplied at construction time
        if plugin in self._extra_deps:
            for d in self._extra_deps[plugin]:
                if d not in deps:
                    deps.append(d)

        for dep in deps:
            if dep != plugin:   # no self-loops
                self._edges[plugin].add(dep)
                self._reverse[dep].add(plugin)
                self._nodes.add(dep)

    def build(self, load_order: List[str]) -> "PluginDependencyGraph":
        """
        Populate the graph from a load order list.

        Returns *self* for chaining.
        """
        for plugin in load_order:
            self.add_plugin(plugin)
        logger.info(
            f"Dependency graph built: {len(self._nodes)} nodes, "
            f"{sum(len(v) for v in self._edges.values())} edges"
        )
        return self

    # ── Analysis ─────────────────────────────────────────────────────

    def get_missing_masters(
        self, plugins: Optional[List[str]] = None
    ) -> List[Tuple[str, str]]:
        """
        Find ``(plugin, missing_master)`` pairs where the required master
        is not in *plugins* (the actual load order), even if it appears
        as an inferred node in the graph.

        Parameters
        ----------
        plugins : list, optional
            The actual load order to check against.  When omitted, checks
            against all nodes — which is useful for pure graph analysis but
            will miss inferred-only deps.

        Returns
        -------
        list of (plugin, missing_master) tuples
        """
        # "Present" means actually in the given list, not just inferred in the graph
        if plugins is not None:
            present = set(plugins)
        else:
            present = set(self._nodes)
        check = set(plugins) if plugins is not None else set(self._nodes)
        result = []
        for plugin in sorted(check):
            for dep in self._edges.get(plugin, set()):
                if dep not in present:
                    result.append((plugin, dep))
        return result

    def get_load_order_violations(
        self, load_order: List[str]
    ) -> List[Tuple[str, str, int, int]]:
        """
        Find ``(plugin, master, plugin_pos, master_pos)`` tuples where
        *plugin* loads at a position *before* its required master.

        Parameters
        ----------
        load_order : list of str
            Ordered list of plugin names.

        Returns
        -------
        list of (plugin, master, plugin_pos, master_pos) tuples
        """
        positions = {name: i for i, name in enumerate(load_order)}
        violations = []
        for plugin in load_order:
            plugin_pos = positions[plugin]
            for dep in self._edges.get(plugin, set()):
                dep_pos = positions.get(dep)
                if dep_pos is not None and dep_pos > plugin_pos:
                    violations.append((plugin, dep, plugin_pos, dep_pos))
        return violations

    def topological_sort(
        self, plugins: Optional[List[str]] = None
    ) -> List[str]:
        """
        Return a valid load order that satisfies all dependency edges using
        Kahn's algorithm (BFS-based topological sort).

        If a cycle is detected the algorithm falls back to the original
        order with the cyclic plugins appended at the end.

        Parameters
        ----------
        plugins : list, optional
            Subset to sort.  Defaults to all nodes, preserving official
            master-file ordering when no dependency is violated.

        Returns
        -------
        list of str
            Topologically ordered plugin names.
        """
        nodes = set(plugins) if plugins is not None else set(self._nodes)
        # In-degree for each node (considering only edges within subset)
        in_deg: Dict[str, int] = {n: 0 for n in nodes}
        for node in nodes:
            for dep in self._edges.get(node, set()):
                if dep in nodes:
                    in_deg[node] += 1

        # Start with nodes that have no dependencies
        queue: deque = deque(
            sorted(n for n, d in in_deg.items() if d == 0)
        )
        result: List[str] = []

        while queue:
            node = queue.popleft()
            result.append(node)
            for dependent in sorted(self._reverse.get(node, set())):
                if dependent in nodes:
                    in_deg[dependent] -= 1
                    if in_deg[dependent] == 0:
                        queue.append(dependent)

        # Cycle fallback: append remaining nodes in original order
        remaining = [n for n in (plugins or sorted(nodes)) if n not in set(result)]
        if remaining:
            logger.warning(
                f"Circular dependency detected — appending {len(remaining)} "
                "plugins in original order: " + ", ".join(remaining[:5])
            )
        return result + remaining

    def dependency_chain(self, plugin: str) -> List[str]:
        """
        Return the full transitive dependency chain for *plugin* in
        load order (masters first).

        Uses BFS to avoid infinite loops from (theoretically impossible)
        cycles.
        """
        visited: Set[str] = set()
        chain: List[str] = []
        queue: deque = deque([plugin])
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            if current != plugin:
                chain.append(current)
            for dep in sorted(self._edges.get(current, set())):
                if dep not in visited:
                    queue.append(dep)
        return chain

    def dependents_of(self, master: str) -> List[str]:
        """
        Return all plugins that (directly) depend on *master*.
        """
        return sorted(self._reverse.get(master, set()))

    def get_statistics(self) -> Dict[str, int]:
        """Return a summary of the graph."""
        return {
            "total_plugins":    len(self._nodes),
            "total_dep_edges":  sum(len(v) for v in self._edges.values()),
            "plugins_with_deps": sum(
                1 for v in self._edges.values() if v
            ),
        }

    def to_dict(self) -> Dict:
        """JSON-serialisable representation of the graph."""
        return {
            "nodes": sorted(self._nodes),
            "edges": {
                k: sorted(v)
                for k, v in self._edges.items()
                if v
            },
        }

    # ── Convenience constructor ───────────────────────────────────────

    @classmethod
    def from_load_order(
        cls,
        load_order: List[str],
        extra_deps: Optional[Dict[str, List[str]]] = None,
    ) -> "PluginDependencyGraph":
        """Shortcut: ``PluginDependencyGraph.from_load_order(my_list)``."""
        graph = cls(extra_deps=extra_deps)
        graph.build(load_order)
        return graph
