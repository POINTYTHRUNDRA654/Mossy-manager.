"""
ModReasoner — Advanced chain-of-thought reasoning engine for Fallout 4 mod management.

Given a load order and/or a set of conflicts this engine works through the
problem *step by step*, producing an auditable reasoning trace that explains:

  • WHY a problem exists (root-cause analysis)
  • WHAT constraints are being violated (dependency / ordering)
  • HOW to fix it (actionable resolution steps)
  • WHAT to do first (priority ranking)

The reasoning is entirely local — no network calls, no API keys.

Design
------
Each call to ``reason()`` or one of the specialised methods returns a
``ReasoningResult`` containing:

  ``steps``       — ordered list of ``ReasoningStep`` objects (the trace)
  ``conclusion``  — the final answer / recommendation in plain English
  ``action_plan`` — ordered list of concrete actions to take
  ``confidence``  — 0–1 score reflecting how certain the engine is

Internally the engine uses a *forward-chaining* strategy:
  1. Gather all facts (load-order positions, conflict data, FO4 rules)
  2. Apply inference rules one by one, recording each deduction as a step
  3. Collect proven conclusions and rank them by severity
  4. Produce an ordered action plan
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from mossy_manager.games.fallout4 import Fallout4Rules

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ReasoningStep:
    """One deductive step in the reasoning trace."""
    step_number: int
    rule: str          # name of the rule / heuristic applied
    observation: str   # what the engine noticed
    deduction: str     # what it concluded from that observation
    severity: str      # info / warning / error / critical
    plugin: Optional[str] = None  # the plugin this step is about (if any)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step_number,
            "rule": self.rule,
            "observation": self.observation,
            "deduction": self.deduction,
            "severity": self.severity,
            "plugin": self.plugin,
        }


@dataclass
class ReasoningResult:
    """Complete output from a reasoning session."""
    problem: str
    steps: List[ReasoningStep] = field(default_factory=list)
    conclusion: str = ""
    action_plan: List[str] = field(default_factory=list)
    confidence: float = 0.0
    severity: str = "info"  # overall severity: info / warning / error / critical

    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem": self.problem,
            "steps": [s.to_dict() for s in self.steps],
            "conclusion": self.conclusion,
            "action_plan": self.action_plan,
            "confidence": self.confidence,
            "severity": self.severity,
            "step_count": len(self.steps),
        }

    def summary(self) -> str:
        """One-paragraph human-readable summary of the reasoning."""
        lines = [f"Problem: {self.problem}", ""]
        for s in self.steps:
            badge = s.severity.upper()
            lines.append(f"  Step {s.step_number} [{badge}] {s.rule}")
            lines.append(f"    Observed : {s.observation}")
            lines.append(f"    Concluded: {s.deduction}")
        lines += ["", f"Conclusion: {self.conclusion}", ""]
        if self.action_plan:
            lines.append("Action Plan:")
            for i, action in enumerate(self.action_plan, 1):
                lines.append(f"  {i}. {action}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Inference rules (each returns a list of ReasoningStep)
# ---------------------------------------------------------------------------

class _Rules:
    """Namespace for all inference-rule functions."""

    @staticmethod
    def rule_master_file_order(
        load_order: List[str], step_offset: int
    ) -> List[ReasoningStep]:
        steps: List[ReasoningStep] = []
        n = step_offset
        positions = {p: i for i, p in enumerate(load_order)}

        for i, master in enumerate(Fallout4Rules.MASTER_FILES):
            if master not in positions:
                continue
            actual = positions[master]
            # Every earlier master must appear before this one
            for prev in Fallout4Rules.MASTER_FILES[:i]:
                if prev not in positions:
                    continue
                if positions[prev] > actual:
                    n += 1
                    steps.append(ReasoningStep(
                        step_number=n,
                        rule="MasterFileOrder",
                        observation=(
                            f"{prev} is at position {positions[prev]} "
                            f"but {master} is at position {actual}"
                        ),
                        deduction=(
                            f"{master} must load AFTER {prev}. "
                            "Move it down in the load order."
                        ),
                        severity="critical",
                        plugin=master,
                    ))
        return steps

    @staticmethod
    def rule_plugin_cap(
        load_order: List[str], step_offset: int
    ) -> List[ReasoningStep]:
        steps: List[ReasoningStep] = []
        slot_plugins = [p for p in load_order if not p.lower().endswith(".esl")]
        count = len(slot_plugins)
        n = step_offset + 1

        if count >= 254:
            steps.append(ReasoningStep(
                step_number=n,
                rule="PluginCapHard",
                observation=f"Slot-consuming plugin count is {count}/255",
                deduction=(
                    "The game WILL NOT LOAD. You must immediately: "
                    "(a) ESL-flag small plugins in FO4Edit, or "
                    "(b) merge plugins with zMerge, or "
                    "(c) disable optional mods."
                ),
                severity="critical",
            ))
        elif count >= 240:
            steps.append(ReasoningStep(
                step_number=n,
                rule="PluginCapWarning",
                observation=f"Slot-consuming plugin count is {count}/255",
                deduction=(
                    f"Only {255 - count} slots remain. "
                    "Identify plugins under 2048 new Form IDs and ESL-flag them "
                    "before adding more mods."
                ),
                severity="warning",
            ))
        return steps

    @staticmethod
    def rule_patch_position(
        load_order: List[str], step_offset: int
    ) -> List[ReasoningStep]:
        """Patches must load after the mods they patch."""
        steps: List[ReasoningStep] = []
        positions = {p: i for i, p in enumerate(load_order)}
        n = step_offset

        patch_keywords = ("patch", "compat", "fix", "bashed", "merged", "smashed")
        for plugin in load_order:
            pl = plugin.lower()
            if not any(kw in pl for kw in patch_keywords):
                continue
            pos = positions[plugin]
            # A patch that loads in the first 30 % of the order is suspicious
            if pos < len(load_order) * 0.3:
                n += 1
                steps.append(ReasoningStep(
                    step_number=n,
                    rule="PatchLoadedTooEarly",
                    observation=(
                        f"'{plugin}' appears at position {pos}/{len(load_order)} "
                        f"({int(100 * pos / max(len(load_order) - 1, 1))}% into the load order)"
                    ),
                    deduction=(
                        f"Patch plugins should load LATE (after the mods they fix). "
                        f"Move '{plugin}' toward the end of the load order."
                    ),
                    severity="warning",
                    plugin=plugin,
                ))
        return steps

    @staticmethod
    def rule_unofficial_patch(
        load_order: List[str], step_offset: int
    ) -> List[ReasoningStep]:
        n = step_offset + 1
        has_ufp = any(
            "unofficial" in p.lower() and "patch" in p.lower()
            for p in load_order
        )
        if not has_ufp:
            return [ReasoningStep(
                step_number=n,
                rule="MissingUFP",
                observation="No Unofficial Fallout 4 Patch (UFO4P) found in load order",
                deduction=(
                    "UFO4P fixes thousands of bugs. Install it from Nexus Mods "
                    "and place it immediately after the official DLC masters."
                ),
                severity="warning",
            )]
        # Check it's near the top
        positions = {p: i for i, p in enumerate(load_order)}
        for p in load_order:
            if "unofficial" in p.lower() and "patch" in p.lower():
                pos = positions[p]
                if pos > 20:
                    return [ReasoningStep(
                        step_number=n,
                        rule="UFPLoadedLate",
                        observation=f"'{p}' is at position {pos}, well after the DLC masters",
                        deduction=(
                            "UFO4P should load immediately after the official DLC masters "
                            f"(positions 0–7). Move '{p}' up."
                        ),
                        severity="warning",
                        plugin=p,
                    )]
        return []

    @staticmethod
    def rule_conflict_chain(
        conflicts: List[Dict[str, Any]],
        load_order: List[str],
        step_offset: int,
    ) -> List[ReasoningStep]:
        """Trace each conflict to its root cause and winning mod."""
        steps: List[ReasoningStep] = []
        n = step_offset
        positions = {p: i for i, p in enumerate(load_order)}

        for conflict in conflicts:
            mods = conflict.get("mods", [])
            resource = conflict.get("resource", "unknown")
            severity = conflict.get("severity", "medium")
            if len(mods) < 2:
                continue

            # Winner = highest position in load order
            winner = max(
                mods,
                key=lambda m: positions.get(m, -1),
                default=mods[0],
            )
            losers = [m for m in mods if m != winner]
            n += 1
            steps.append(ReasoningStep(
                step_number=n,
                rule="ConflictRootCause",
                observation=(
                    f"Resource '{resource}' is claimed by {len(mods)} mods: "
                    + ", ".join(mods)
                ),
                deduction=(
                    f"Winner (last in load order): '{winner}'. "
                    f"Overridden: {', '.join(losers)}. "
                    + (
                        "This is a SCRIPT conflict — consider a compatibility patch. "
                        if severity in ("high", "critical") else
                        "Adjust load order if the wrong mod is winning."
                    )
                ),
                severity=severity,
                plugin=winner,
            ))
        return steps

    @staticmethod
    def rule_dependency_check(
        load_order: List[str], step_offset: int
    ) -> List[ReasoningStep]:
        """Check known dependencies using FO4 rule knowledge."""
        steps: List[ReasoningStep] = []
        positions = {p.lower(): i for i, p in enumerate(load_order)}
        n = step_offset

        for plugin in load_order:
            deps = Fallout4Rules.get_plugin_dependencies(plugin)
            for dep in deps:
                if dep.lower() not in positions:
                    n += 1
                    steps.append(ReasoningStep(
                        step_number=n,
                        rule="MissingDependency",
                        observation=f"'{plugin}' requires '{dep}' but it is not in the load order",
                        deduction=(
                            f"Install '{dep}' and place it BEFORE '{plugin}' in the load order. "
                            "Without its master, the game may crash on startup."
                        ),
                        severity="critical",
                        plugin=plugin,
                    ))
        return steps

    @staticmethod
    def rule_missing_master(
        load_order: List[str], step_offset: int
    ) -> List[ReasoningStep]:
        """
        Use PluginDependencyGraph to detect:
        (a) masters absent from the load order entirely, and
        (b) plugins that load BEFORE their required master.
        """
        try:
            from mossy_manager.core.dependency_graph import PluginDependencyGraph
        except ImportError:
            return []

        graph = PluginDependencyGraph.from_load_order(load_order)
        steps: List[ReasoningStep] = []
        n = step_offset
        seen: set = set()

        # (a) Missing from load order
        for plugin, master in graph.get_missing_masters(load_order):
            key = (plugin, master)
            if key in seen:
                continue
            seen.add(key)
            n += 1
            steps.append(ReasoningStep(
                step_number=n,
                rule="MissingMaster",
                observation=(
                    f"'{plugin}' requires master '{master}' "
                    "which is absent from the load order"
                ),
                deduction=(
                    f"Install '{master}' and ensure it loads before '{plugin}'. "
                    "A missing master causes an instant crash on game start."
                ),
                severity="critical",
                plugin=plugin,
            ))

        # (b) Load-order violations (plugin before its master)
        for plugin, master, p_pos, m_pos in graph.get_load_order_violations(load_order):
            key = f"viol_{plugin}_{master}"
            if key in seen:
                continue
            seen.add(key)
            n += 1
            steps.append(ReasoningStep(
                step_number=n,
                rule="MasterLoadedLate",
                observation=(
                    f"'{plugin}' is at position {p_pos} but its master "
                    f"'{master}' is at position {m_pos} — master loads after plugin"
                ),
                deduction=(
                    f"Move '{master}' to before '{plugin}' in the load order. "
                    "Masters must always precede every plugin that depends on them."
                ),
                severity="critical",
                plugin=plugin,
            ))

        return steps

    @staticmethod
    def rule_f4se_check(
        load_order: List[str], step_offset: int
    ) -> List[ReasoningStep]:
        n = step_offset
        f4se_mods = [
            p for p in load_order
            if "f4se" in p.lower() or "mcm" in p.lower()
        ]
        if f4se_mods:
            n += 1
            return [ReasoningStep(
                step_number=n,
                rule="F4SEDependency",
                observation=(
                    f"{len(f4se_mods)} F4SE-dependent plugin(s) detected: "
                    + ", ".join(f4se_mods[:3])
                    + (" ..." if len(f4se_mods) > 3 else "")
                ),
                deduction=(
                    "Ensure Fallout 4 Script Extender (F4SE) is installed and "
                    "matches your exact game version. Launch via f4se_loader.exe, "
                    "NOT the vanilla launcher or Steam."
                ),
                severity="info",
            )]
        return []


# ---------------------------------------------------------------------------
# Public reasoner class
# ---------------------------------------------------------------------------

class ModReasoner:
    """
    Chain-of-thought reasoning engine for Fallout 4 mod management.

    Usage
    -----
    ::

        reasoner = ModReasoner()

        # Reason about a full load order
        result = reasoner.reason_about_load_order(load_order)
        print(result.summary())

        # Reason about a specific conflict
        result = reasoner.reason_about_conflict(conflict_dict, load_order)

        # Diagnose a crash / problem description
        result = reasoner.diagnose(problem_text, load_order)
    """

    def __init__(self) -> None:
        self._rules = _Rules()

    # ------------------------------------------------------------------ #
    #  Main entry points                                                  #
    # ------------------------------------------------------------------ #

    def reason_about_load_order(
        self,
        load_order: List[str],
        conflicts: Optional[List[Dict[str, Any]]] = None,
    ) -> ReasoningResult:
        """
        Comprehensively reason about a full Fallout 4 load order.

        Parameters
        ----------
        load_order : list of str
            Ordered list of plugin names (same order as loadorder.txt).
        conflicts : list of dicts, optional
            Conflicts previously detected by ``ConflictResolver``.

        Returns
        -------
        ReasoningResult
            Full trace with steps, conclusion, and action plan.
        """
        problem = f"Analyse load order of {len(load_order)} plugins"
        result = ReasoningResult(problem=problem)

        # Run all inference rules in priority order
        all_steps: List[ReasoningStep] = []
        offset = 0

        # Rule 1 — master file ordering (hard rules)
        steps = _Rules.rule_master_file_order(load_order, offset)
        all_steps.extend(steps); offset = len(all_steps)

        # Rule 2 — plugin cap
        steps = _Rules.rule_plugin_cap(load_order, offset)
        all_steps.extend(steps); offset = len(all_steps)

        # Rule 3 — missing dependency (heuristic name-based)
        steps = _Rules.rule_dependency_check(load_order, offset)
        all_steps.extend(steps); offset = len(all_steps)

        # Rule 3b — missing master / load-order violation (graph-based)
        steps = _Rules.rule_missing_master(load_order, offset)
        all_steps.extend(steps); offset = len(all_steps)

        # Rule 4 — unofficial patch
        steps = _Rules.rule_unofficial_patch(load_order, offset)
        all_steps.extend(steps); offset = len(all_steps)

        # Rule 5 — patch position
        steps = _Rules.rule_patch_position(load_order, offset)
        all_steps.extend(steps); offset = len(all_steps)

        # Rule 6 — F4SE
        steps = _Rules.rule_f4se_check(load_order, offset)
        all_steps.extend(steps); offset = len(all_steps)

        # Rule 7 — conflict chains (if provided)
        if conflicts:
            steps = _Rules.rule_conflict_chain(conflicts, load_order, offset)
            all_steps.extend(steps)

        result.steps = all_steps
        result.conclusion, result.action_plan, result.confidence, result.severity = (
            self._synthesise(all_steps, load_order)
        )
        return result

    def reason_about_conflict(
        self,
        conflict: Dict[str, Any],
        load_order: List[str],
    ) -> ReasoningResult:
        """
        Deep-dive reasoning about a *single* conflict.

        Returns the root cause, the winning mod, and what to do about it.
        """
        resource = conflict.get("resource", "unknown resource")
        problem = f"Resolve conflict on '{resource}'"
        result = ReasoningResult(problem=problem)

        steps = _Rules.rule_conflict_chain([conflict], load_order, 0)

        # Additional: check if a patch is already present
        mods = conflict.get("mods", [])
        n = len(steps) + 1
        patch_present = any(
            "patch" in p.lower() or "compat" in p.lower()
            for p in load_order
        )
        if not patch_present and len(mods) >= 2:
            steps.append(ReasoningStep(
                step_number=n,
                rule="NoPatchPresent",
                observation=(
                    f"No compatibility patch found in load order for conflict "
                    f"between {mods[0]} and {mods[1]}"
                ),
                deduction=(
                    "Create a new patch plugin in FO4Edit: load both mods, "
                    f"forward the winning '{resource}' record into a new .esp, "
                    "then place the patch AFTER both conflicting mods."
                ),
                severity="warning",
                plugin=None,
            ))

        result.steps = steps
        result.conclusion, result.action_plan, result.confidence, result.severity = (
            self._synthesise(steps, load_order)
        )
        return result

    def diagnose(
        self,
        problem_description: str,
        load_order: Optional[List[str]] = None,
    ) -> ReasoningResult:
        """
        Diagnose a problem from a free-text description.

        The engine pattern-matches keywords to known Fallout 4 failure modes
        and constructs a targeted reasoning trace.

        Parameters
        ----------
        problem_description : str
            Plain-English description of the problem (crash, missing texture,
            invisible NPC, CTD on load, etc.).
        load_order : list of str, optional
            Current load order for context-aware diagnosis.
        """
        desc = problem_description.lower()
        lo = load_order or []
        result = ReasoningResult(problem=problem_description)
        steps: List[ReasoningStep] = []
        n = 0

        # ── Pattern: CTD / crash ─────────────────────────────────────
        if any(kw in desc for kw in ("ctd", "crash", "freeze", "stop working")):
            n += 1
            steps.append(ReasoningStep(
                step_number=n, rule="CrashDiagnosis",
                observation="Problem description mentions a crash or CTD",
                deduction=(
                    "Most Fallout 4 CTDs on load are caused by: "
                    "(1) missing master file, "
                    "(2) plugin cap exceeded (255 slots), "
                    "(3) a corrupt/outdated plugin, or "
                    "(4) conflicting script mods. "
                    "Start by checking the plugin count and verifying all masters are present."
                ),
                severity="critical",
            ))
            if lo:
                cap_steps = _Rules.rule_plugin_cap(lo, n)
                steps.extend(cap_steps); n = len(steps)
                dep_steps = _Rules.rule_dependency_check(lo, n)
                steps.extend(dep_steps); n = len(steps)

        # ── Pattern: missing texture / purple mesh ───────────────────
        if any(kw in desc for kw in ("purple", "missing texture", "pink", "invisible mesh")):
            n += 1
            steps.append(ReasoningStep(
                step_number=n, rule="MissingTextureDiagnosis",
                observation="Problem description mentions missing textures or purple/pink objects",
                deduction=(
                    "This is a texture path conflict or missing BA2 archive. "
                    "Check that: (a) the mod providing the texture is installed and enabled, "
                    "(b) no other mod is overwriting the texture with a wrong path, "
                    "(c) BA2 archives are not corrupt (verify in MO2)."
                ),
                severity="warning",
            ))

        # ── Pattern: script lag / stuttering ────────────────────────
        if any(kw in desc for kw in ("lag", "stutter", "slow", "script", "papyrus")):
            n += 1
            steps.append(ReasoningStep(
                step_number=n, rule="ScriptLagDiagnosis",
                observation="Problem description mentions script lag or stuttering",
                deduction=(
                    "Script lag is caused by too many or poorly written scripts running "
                    "simultaneously. Check the Papyrus log "
                    "(Documents/My Games/Fallout4/Logs/Script/Papyrus.0.log) for "
                    "stack dumps. Disable script-heavy mods one at a time to isolate the cause."
                ),
                severity="warning",
            ))
            if lo:
                f4se_steps = _Rules.rule_f4se_check(lo, n)
                steps.extend(f4se_steps); n = len(steps)

        # ── Pattern: load order ──────────────────────────────────────
        if any(kw in desc for kw in ("load order", "wrong mod winning", "overridden")):
            n += 1
            steps.append(ReasoningStep(
                step_number=n, rule="LoadOrderDiagnosis",
                observation="Problem description mentions incorrect load order behaviour",
                deduction=(
                    "In MO2 the last plugin in loadorder.txt wins for any given record. "
                    "Use 'mossy loadorder optimize' to sort by category, or manually "
                    "drag the desired winner to a later position."
                ),
                severity="info",
            ))
            if lo:
                patch_steps = _Rules.rule_patch_position(lo, n)
                steps.extend(patch_steps); n = len(steps)

        # ── Fallback ─────────────────────────────────────────────────
        if not steps:
            n += 1
            steps.append(ReasoningStep(
                step_number=n, rule="GenericDiagnosis",
                observation=f"Problem: '{problem_description[:120]}'",
                deduction=(
                    "No specific pattern matched. Recommended workflow: "
                    "(1) Run 'mossy auto --apply' to optimize and scan for conflicts, "
                    "(2) Run 'mossy ai analyze' for AI-powered recommendations, "
                    "(3) Check the Papyrus log and the MO2 log for error messages."
                ),
                severity="info",
            ))

        result.steps = steps
        result.conclusion, result.action_plan, result.confidence, result.severity = (
            self._synthesise(steps, lo)
        )
        return result

    # ------------------------------------------------------------------ #
    #  Private synthesis                                                  #
    # ------------------------------------------------------------------ #

    def _synthesise(
        self,
        steps: List[ReasoningStep],
        load_order: List[str],
    ) -> Tuple[str, List[str], float, str]:
        """
        Turn a list of reasoning steps into a conclusion, action plan,
        confidence score, and overall severity.
        """
        if not steps:
            return (
                "No issues detected. Load order appears healthy.",
                ["No immediate action required."],
                0.95,
                "info",
            )

        # Severity hierarchy
        sev_rank = {"info": 0, "warning": 1, "error": 2, "critical": 3}
        worst = max(steps, key=lambda s: sev_rank.get(s.severity, 0))
        overall_sev = worst.severity

        # Confidence: higher when more rules fire, capped at 0.95
        base_confidence = min(0.5 + 0.05 * len(steps), 0.95)

        # Build action plan — one action per unique deduction
        seen: set = set()
        actions: List[str] = []
        # Sort steps: critical first, then warning, info
        sorted_steps = sorted(
            steps, key=lambda s: -sev_rank.get(s.severity, 0)
        )
        for s in sorted_steps:
            key = s.rule
            if key not in seen:
                seen.add(key)
                actions.append(s.deduction)

        # Conclusion
        critical_count = sum(1 for s in steps if s.severity == "critical")
        warning_count  = sum(1 for s in steps if s.severity == "warning")
        if critical_count:
            conclusion = (
                f"Found {critical_count} critical issue(s) that will prevent the game "
                f"from loading correctly. Address them immediately (see action plan)."
            )
        elif warning_count:
            conclusion = (
                f"Load order is functional but has {warning_count} warning(s). "
                "Addressing them will improve stability."
            )
        else:
            conclusion = (
                "Load order passes all checks. Only informational notes remain."
            )

        return conclusion, actions, base_confidence, overall_sev
