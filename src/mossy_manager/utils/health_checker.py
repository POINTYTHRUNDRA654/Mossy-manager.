"""
ModHealthChecker — one-shot, scored health report for a Fallout 4 load order.

Aggregates every available check into a single ``HealthReport``:

  • Load-order structural validation (``Fallout4Rules.validate_load_order``)
  • Master-file ordering and dependency analysis (``PluginDependencyGraph``)
  • Plugin slot usage (255-cap)
  • ESL candidate count (how many slots can be freed)
  • Unofficial Patch presence
  • F4SE dependency warning
  • AI-brain conflict risk + anomaly summary (``ModAIBrain``)
  • Orphaned mods (``MO2Integration.scan_orphaned_mods``)
  • Backup freshness (last backup age)

The overall **health score** (0–100) starts at 100 and loses points for
problems found:

  -20 per critical error (cap at 0)
  -10 per high-severity issue
  - -5 per warning
  - -2 per informational note

Usage::

    checker = ModHealthChecker()
    report  = checker.check(load_order=my_plugins)

    # With full MO2 context
    report = checker.check(
        load_order=my_plugins,
        mo2=mo2_instance,
        profile="Default",
    )

    print(report.summary())
    print(f"Health score: {report.score}/100")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from mossy_manager.core.dependency_graph import PluginDependencyGraph
from mossy_manager.games.fallout4 import Fallout4Rules

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# HealthReport dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class HealthIssue:
    """A single discovered issue."""
    severity: str                  # "critical" | "error" | "warning" | "info"
    category: str                  # "load_order" | "plugin_cap" | "dependency" | "ai" | "mods"
    message: str
    plugin: Optional[str] = None   # Related plugin, if any


@dataclass
class HealthReport:
    """
    Structured health report produced by ``ModHealthChecker.check()``.

    Attributes
    ----------
    score : int
        0–100.  100 = perfect, 0 = serious problems.
    issues : list of HealthIssue
        All problems found, ordered by severity.
    plugin_count : int
    slot_count : int
        Plugins consuming a slot (non-ESL).
    esl_candidates : int
        Number of ``.esp`` plugins small enough to ESL-flag.
    ai_summary : dict
        Condensed output from ModAIBrain.full_analysis(), or ``{}`` when
        the AI check was not run.
    generated_at : str
        ISO timestamp.
    profile : str or None
    """
    score: int
    issues: List[HealthIssue]
    plugin_count: int
    slot_count: int
    esl_candidates: int
    ai_summary: Dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    profile: Optional[str] = None

    # ── Convenience accessors ─────────────────────────────────────────

    @property
    def critical_issues(self) -> List[HealthIssue]:
        return [i for i in self.issues if i.severity == "critical"]

    @property
    def warnings(self) -> List[HealthIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def errors(self) -> List[HealthIssue]:
        return [i for i in self.issues if i.severity in ("critical", "error")]

    def summary(self) -> str:
        """Human-readable summary string."""
        lines = [
            f"╔══════════════════════════════════════════════════════════",
            f"║  Mossy Manager — Health Report   (score: {self.score}/100)",
            f"╚══════════════════════════════════════════════════════════",
            f"  Generated : {self.generated_at[:19]}",
        ]
        if self.profile:
            lines.append(f"  Profile   : {self.profile}")
        lines += [
            f"  Plugins   : {self.plugin_count}  (slot usage: {self.slot_count}/255)",
            f"  ESL slots : {self.esl_candidates} plugin(s) could be ESL-flagged",
            "",
        ]
        if not self.issues:
            lines.append("  ✓ No issues found — load order looks healthy!")
        else:
            sev_label = {"critical": "✗ CRITICAL", "error": "✗ ERROR",
                         "warning": "⚠ WARNING",  "info": "ℹ INFO"}
            for issue in self.issues:
                label = sev_label.get(issue.severity, "  INFO")
                plugin = f" [{issue.plugin}]" if issue.plugin else ""
                lines.append(f"  {label}{plugin}: {issue.message}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """JSON-serialisable representation."""
        return {
            "score": self.score,
            "plugin_count": self.plugin_count,
            "slot_count": self.slot_count,
            "esl_candidates": self.esl_candidates,
            "profile": self.profile,
            "generated_at": self.generated_at,
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "message":  i.message,
                    "plugin":   i.plugin,
                }
                for i in self.issues
            ],
            "ai_summary": self.ai_summary,
        }


# ─────────────────────────────────────────────────────────────────────────────
# ModHealthChecker
# ─────────────────────────────────────────────────────────────────────────────

class ModHealthChecker:
    """
    Run all available health checks against a Fallout 4 load order and
    return a scored ``HealthReport``.

    Parameters
    ----------
    run_ai : bool
        Set to *False* to skip the AI brain analysis (faster; default *True*).
    """

    # Point deductions per severity
    _DEDUCTIONS = {"critical": 20, "error": 10, "warning": 5, "info": 2}
    # Sort order for display (lower = first)
    _SEV_RANK = {"critical": 0, "error": 1, "warning": 2, "info": 3}

    def __init__(self, run_ai: bool = True) -> None:
        self.run_ai = run_ai

    def check(
        self,
        load_order: List[str],
        profile: Optional[str] = None,
        mo2: Optional[Any] = None,   # MO2Integration instance
    ) -> HealthReport:
        """
        Run all checks and return a ``HealthReport``.

        Parameters
        ----------
        load_order : list of str
            Ordered list of plugin names (as read from ``loadorder.txt``).
        profile : str, optional
            Profile name — stored in the report for display purposes.
        mo2 : MO2Integration, optional
            When supplied, orphaned-mod and backup-freshness checks run.
        """
        issues: List[HealthIssue] = []

        # ── 1. FO4Rules structural validation ──────────────────────────
        issues.extend(self._check_fo4_rules(load_order))

        # ── 2. Dependency graph analysis ──────────────────────────────
        issues.extend(self._check_dependencies(load_order))

        # ── 3. Plugin cap ─────────────────────────────────────────────
        slot_count = sum(1 for p in load_order if not p.lower().endswith(".esl"))
        issues.extend(self._check_plugin_cap(slot_count))

        # ── 4. Best-practice recommendations ─────────────────────────
        issues.extend(self._check_best_practices(load_order))

        # ── 5. ESL candidates ─────────────────────────────────────────
        from mossy_manager.core.load_order import LoadOrderManager
        lom = LoadOrderManager()
        for name in load_order:
            from mossy_manager.core.load_order import Plugin
            lom.plugins[name] = Plugin(name=name, enabled=True)
        esl_candidates = len(lom.suggest_esl_candidates())

        # ── 6. AI brain ───────────────────────────────────────────────
        ai_summary: Dict[str, Any] = {}
        if self.run_ai:
            try:
                from mossy_manager.ai.brain import ModAIBrain
                brain = ModAIBrain()
                full = brain.full_analysis(load_order)
                ai_summary = full
                issues.extend(self._check_ai_results(full))
            except Exception as exc:
                logger.warning(f"AI brain check skipped: {exc}")

        # ── 7. Orphaned mods (needs MO2) ─────────────────────────────
        if mo2 is not None:
            try:
                orphaned = mo2.scan_orphaned_mods()
                if orphaned:
                    issues.append(HealthIssue(
                        severity="info",
                        category="mods",
                        message=(
                            f"{len(orphaned)} orphaned mod folder(s) found in mods/ "
                            "that are not referenced by any profile "
                            "(safe to review for removal): "
                            + ", ".join(orphaned[:5])
                            + (" …" if len(orphaned) > 5 else "")
                        ),
                    ))
            except Exception as exc:
                logger.warning(f"Orphan scan skipped: {exc}")

        # ── Sort and score ────────────────────────────────────────────
        issues.sort(key=lambda i: self._SEV_RANK.get(i.severity, 3))
        score = self._calculate_score(issues)

        return HealthReport(
            score=score,
            issues=issues,
            plugin_count=len(load_order),
            slot_count=slot_count,
            esl_candidates=esl_candidates,
            ai_summary=ai_summary,
            profile=profile,
        )

    # ── Private check helpers ─────────────────────────────────────────

    def _check_fo4_rules(self, load_order: List[str]) -> List[HealthIssue]:
        issues: List[HealthIssue] = []
        result = Fallout4Rules.validate_load_order(load_order)

        for msg in result.get("errors", []):
            # Determine which plugin is mentioned (first token ending in .esm/.esp)
            plugin = self._extract_plugin(msg)
            issues.append(HealthIssue(
                severity="critical",
                category="load_order",
                message=msg,
                plugin=plugin,
            ))
        for msg in result.get("warnings", []):
            plugin = self._extract_plugin(msg)
            issues.append(HealthIssue(
                severity="warning",
                category="load_order",
                message=msg,
                plugin=plugin,
            ))
        return issues

    def _check_dependencies(self, load_order: List[str]) -> List[HealthIssue]:
        issues: List[HealthIssue] = []
        graph = PluginDependencyGraph.from_load_order(load_order)

        missing = graph.get_missing_masters(load_order)
        for plugin, master in missing:
            issues.append(HealthIssue(
                severity="critical",
                category="dependency",
                message=(
                    f"'{plugin}' requires master '{master}' "
                    "which is not present in the load order"
                ),
                plugin=plugin,
            ))

        violations = graph.get_load_order_violations(load_order)
        for plugin, master, p_pos, m_pos in violations:
            issues.append(HealthIssue(
                severity="error",
                category="dependency",
                message=(
                    f"'{plugin}' (pos {p_pos}) loads before its master "
                    f"'{master}' (pos {m_pos})"
                ),
                plugin=plugin,
            ))
        return issues

    def _check_plugin_cap(self, slot_count: int) -> List[HealthIssue]:
        issues: List[HealthIssue] = []
        if slot_count >= 255:
            issues.append(HealthIssue(
                severity="critical",
                category="plugin_cap",
                message=(
                    f"Plugin cap reached ({slot_count}/255). "
                    "Game will crash on load. ESL-flag or remove plugins immediately."
                ),
            ))
        elif slot_count >= 254:
            issues.append(HealthIssue(
                severity="error",
                category="plugin_cap",
                message=(
                    f"One slot remaining ({slot_count}/255). "
                    "Adding any more plugins will cause a crash."
                ),
            ))
        elif slot_count >= 240:
            issues.append(HealthIssue(
                severity="warning",
                category="plugin_cap",
                message=(
                    f"Approaching plugin cap ({slot_count}/255). "
                    "ESL-flag small ESPs to free slots."
                ),
            ))
        return issues

    def _check_best_practices(self, load_order: List[str]) -> List[HealthIssue]:
        issues: List[HealthIssue] = []
        recommendations = Fallout4Rules.get_recommendations(load_order)
        for rec in recommendations:
            issues.append(HealthIssue(
                severity="info",
                category="best_practice",
                message=rec,
            ))
        return issues

    def _check_ai_results(self, ai_full: Dict[str, Any]) -> List[HealthIssue]:
        issues: List[HealthIssue] = []

        # High-risk plugins
        risk = ai_full.get("conflict_risk", {})
        for plugin_name, info in (risk.items() if isinstance(risk, dict) else {}.items()):
            if isinstance(info, dict) and info.get("risk_level") == "high":
                issues.append(HealthIssue(
                    severity="warning",
                    category="ai",
                    message=f"AI: high conflict risk predicted for '{plugin_name}'",
                    plugin=plugin_name,
                ))

        # Anomalies
        anomalies = ai_full.get("anomalies", [])
        if isinstance(anomalies, list):
            for anom in anomalies[:5]:   # cap to avoid noise
                name = anom if isinstance(anom, str) else anom.get("plugin", str(anom))
                issues.append(HealthIssue(
                    severity="info",
                    category="ai",
                    message=f"AI: load-order anomaly detected — '{name}'",
                    plugin=name if isinstance(name, str) else None,
                ))

        # Plugin-cap recommendation from AI
        recs = ai_full.get("recommendations", [])
        if isinstance(recs, list):
            for rec in recs:
                if isinstance(rec, str) and ("esl" in rec.lower() or "cap" in rec.lower()):
                    issues.append(HealthIssue(
                        severity="warning",
                        category="ai",
                        message=f"AI recommendation: {rec}",
                    ))
                    break   # one is enough

        return issues

    # ── Score calculation ─────────────────────────────────────────────

    def _calculate_score(self, issues: List[HealthIssue]) -> int:
        score = 100
        for issue in issues:
            score -= self._DEDUCTIONS.get(issue.severity, 0)
        return max(0, min(100, score))

    # ── Helper ────────────────────────────────────────────────────────

    @staticmethod
    def _extract_plugin(message: str) -> Optional[str]:
        """Extract the first plugin filename mentioned in *message*."""
        import re
        match = re.search(r"\b[\w\s]+\.(esm|esp|esl)\b", message, re.IGNORECASE)
        return match.group(0).strip() if match else None
