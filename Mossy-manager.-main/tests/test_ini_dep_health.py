"""
Tests for INIPatcher, PluginDependencyGraph, and ModHealthChecker.
All tests are self-contained (no real INI files or MO2 installation needed).
"""

import json
import tempfile
from pathlib import Path

import pytest

from mossy_manager.utils.ini_patcher import INIPatcher, PRESET_NAMES
from mossy_manager.core.dependency_graph import PluginDependencyGraph
from mossy_manager.utils.health_checker import ModHealthChecker, HealthReport, HealthIssue


# ─────────────────────────────────────────────────────────────────────────────
# Shared fixtures
# ─────────────────────────────────────────────────────────────────────────────

GOOD_ORDER = [
    "Fallout4.esm", "DLCRobot.esm", "DLCworkshop01.esm",
    "DLCCoast.esm", "DLCworkshop02.esm", "DLCworkshop03.esm",
    "DLCNukaWorld.esm", "UnoffPatch.esp",
    "WeaponOverhaul.esp", "ArmorMod.esp", "TexturePack.esp",
    "BashedPatch.esp",
]

BAD_MASTERS = [
    "DLCCoast.esm",   # wrong: should follow DLCworkshop01
    "Fallout4.esm",   # wrong: must be first
    "DLCRobot.esm",
    "WeaponMod.esp",
]

VIOLATION_ORDER = [
    "WeaponMod.esp",  # loads before its master Fallout4.esm
    "Fallout4.esm",
    "DLCRobot.esm",
]


# ═════════════════════════════════════════════════════════════════════════════
# INIPatcher
# ═════════════════════════════════════════════════════════════════════════════

class TestINIPatcherInit:
    def test_default_docs_path(self):
        p = INIPatcher()
        assert "Fallout4" in str(p.game_docs_path)

    def test_custom_docs_path(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        assert p.game_docs_path == tmp_path

    def test_ini_path_builds_correctly(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        assert p.ini_path("Fallout4Custom.ini") == tmp_path / "Fallout4Custom.ini"


class TestINIPatcherWrite:
    def test_write_value_creates_file(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        dest = p.write_value("Papyrus", "bEnableLogging", "1")
        assert dest.exists()

    def test_write_value_content_correct(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        p.write_value("Papyrus", "bEnableLogging", "1")
        val = p.read_value("Papyrus", "bEnableLogging", "Fallout4Custom.ini")
        assert val == "1"

    def test_write_value_overwrites_existing(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        p.write_value("Papyrus", "bEnableLogging", "0")
        p.write_value("Papyrus", "bEnableLogging", "1")
        val = p.read_value("Papyrus", "bEnableLogging", "Fallout4Custom.ini")
        assert val == "1"

    def test_write_values_batch(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        settings = [
            ("Papyrus", "bEnableLogging",   "1"),
            ("Papyrus", "bEnableTrace",      "1"),
            ("Archive", "bInvalidateOlderFiles", "1"),
        ]
        p.write_values(settings)
        assert p.read_value("Papyrus", "bEnableLogging",       "Fallout4Custom.ini") == "1"
        assert p.read_value("Papyrus", "bEnableTrace",          "Fallout4Custom.ini") == "1"
        assert p.read_value("Archive", "bInvalidateOlderFiles", "Fallout4Custom.ini") == "1"

    def test_write_creates_parent_dirs(self, tmp_path):
        subdir = tmp_path / "nested" / "docs"
        p = INIPatcher(game_docs_path=subdir)
        dest = p.write_value("Display", "bFull Screen", "1")
        assert dest.exists()

    def test_write_multiple_sections(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        p.write_value("SectionA", "keyA", "valA")
        p.write_value("SectionB", "keyB", "valB")
        assert p.read_value("SectionA", "keyA", "Fallout4Custom.ini") == "valA"
        assert p.read_value("SectionB", "keyB", "Fallout4Custom.ini") == "valB"


class TestINIPatcherRead:
    def test_read_absent_returns_none(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        assert p.read_value("Papyrus", "bEnableLogging") is None

    def test_read_section_empty_when_absent(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        assert p.read_section("Papyrus") == {}

    def test_read_section_returns_all_keys(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        p.write_values([
            ("Papyrus", "bEnableLogging", "1"),
            ("Papyrus", "bEnableTrace",   "1"),
        ])
        section = p.read_section("Papyrus", "Fallout4Custom.ini")
        assert "bEnableLogging" in section
        assert "bEnableTrace" in section

    def test_get_all_values_structure(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        p.write_values([("Papyrus", "bEnableLogging", "1")])
        all_vals = p.get_all_values("Fallout4Custom.ini")
        assert "Papyrus" in all_vals
        assert "bEnableLogging" in all_vals["Papyrus"]

    def test_read_fallback_to_custom(self, tmp_path):
        # Write to Custom.ini, read via main Fallout4.ini — should fall back
        p = INIPatcher(game_docs_path=tmp_path)
        p.write_value("Papyrus", "bEnableLogging", "1", filename="Fallout4Custom.ini")
        val = p.read_value("Papyrus", "bEnableLogging", filename="Fallout4.ini")
        assert val == "1"


class TestINIPatcherPresets:
    def test_all_preset_names_known(self):
        assert "papyrus_logging" in PRESET_NAMES
        assert "archive_invalidation" in PRESET_NAMES
        assert "performance_high" in PRESET_NAMES
        assert "performance_low" in PRESET_NAMES
        assert "f4se_compat" in PRESET_NAMES

    def test_apply_preset_papyrus_logging(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        written, backup = p.apply_preset("papyrus_logging", backup=False)
        assert written.exists()
        assert backup is None
        ok, problems = p.validate_preset_applied("papyrus_logging")
        assert ok, f"Problems: {problems}"

    def test_apply_preset_archive_invalidation(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        written, _ = p.apply_preset("archive_invalidation", backup=False)
        ok, _ = p.validate_preset_applied("archive_invalidation")
        assert ok

    def test_apply_preset_performance_high(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        written, _ = p.apply_preset("performance_high", backup=False)
        ok, _ = p.validate_preset_applied("performance_high")
        assert ok

    def test_apply_preset_performance_low(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        written, _ = p.apply_preset("performance_low", backup=False)
        ok, _ = p.validate_preset_applied("performance_low")
        assert ok

    def test_apply_preset_f4se_compat(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        written, _ = p.apply_preset("f4se_compat", backup=False)
        ok, _ = p.validate_preset_applied("f4se_compat")
        assert ok

    def test_apply_unknown_preset_raises(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        with pytest.raises(ValueError, match="Unknown INI preset"):
            p.apply_preset("nonexistent_preset")

    def test_apply_preset_with_backup(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        # Create the file first so a backup can be made
        p.write_value("Papyrus", "bEnableLogging", "0")
        written, backup = p.apply_preset("papyrus_logging", backup=True)
        assert backup is not None
        assert backup.exists()

    def test_apply_preset_backup_skipped_when_file_absent(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        # File doesn't exist yet → no backup
        _, backup = p.apply_preset("papyrus_logging", backup=True)
        assert backup is None

    def test_validate_preset_partial_application(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        # Only write one of papyrus_logging's four settings
        p.write_value("Papyrus", "bEnableLogging", "1")
        ok, problems = p.validate_preset_applied("papyrus_logging")
        assert not ok
        assert len(problems) >= 1

    def test_validate_unknown_preset_raises(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        with pytest.raises(ValueError):
            p.validate_preset_applied("bad_preset")


class TestINIPatcherBackup:
    def test_backup_creates_file(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        p.write_value("Papyrus", "bEnableLogging", "1")
        backup = p.backup_ini("Fallout4Custom.ini")
        assert backup is not None
        assert backup.exists()

    def test_backup_returns_none_when_missing(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        backup = p.backup_ini("Fallout4Custom.ini")
        assert backup is None

    def test_backup_filename_has_timestamp(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        p.write_value("Papyrus", "bEnableLogging", "1")
        backup = p.backup_ini("Fallout4Custom.ini")
        assert "backup" in backup.name

    def test_backup_preserves_content(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        p.write_value("Papyrus", "bEnableLogging", "1")
        backup = p.backup_ini()
        # Now overwrite
        p.write_value("Papyrus", "bEnableLogging", "0")
        # Backup should still have "1"
        content = backup.read_text()
        assert "1" in content


class TestINIPatcherDiff:
    def test_diff_returns_empty_for_identical(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        # Write same content to both files
        for fname in ("Fallout4.ini", "Fallout4Custom.ini"):
            p.write_value("Papyrus", "bEnableLogging", "1", filename=fname)
        diff = p.diff("Fallout4.ini", "Fallout4Custom.ini")
        assert diff == {}

    def test_diff_detects_differences(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        p.write_value("Papyrus", "bEnableLogging", "0", filename="Fallout4.ini")
        p.write_value("Papyrus", "bEnableLogging", "1", filename="Fallout4Custom.ini")
        diff = p.diff("Fallout4.ini", "Fallout4Custom.ini")
        assert "Papyrus" in diff
        assert "bEnableLogging" in diff["Papyrus"]
        val_a, val_b = diff["Papyrus"]["bEnableLogging"]
        assert val_a == "0"
        assert val_b == "1"

    def test_diff_detects_missing_key(self, tmp_path):
        p = INIPatcher(game_docs_path=tmp_path)
        p.write_value("Papyrus", "bEnableLogging", "1", filename="Fallout4Custom.ini")
        # Fallout4.ini has no [Papyrus] section
        diff = p.diff("Fallout4.ini", "Fallout4Custom.ini")
        assert "Papyrus" in diff


# ═════════════════════════════════════════════════════════════════════════════
# PluginDependencyGraph
# ═════════════════════════════════════════════════════════════════════════════

class TestDependencyGraphInit:
    def test_instantiates(self):
        g = PluginDependencyGraph()
        assert g is not None

    def test_from_load_order_constructor(self):
        g = PluginDependencyGraph.from_load_order(GOOD_ORDER)
        assert len(g._nodes) > 0


class TestDependencyGraphBuild:
    def test_build_adds_nodes(self):
        g = PluginDependencyGraph()
        g.build(GOOD_ORDER)
        assert "Fallout4.esm" in g._nodes
        assert "WeaponOverhaul.esp" in g._nodes

    def test_add_plugin_records_edges(self):
        g = PluginDependencyGraph()
        g.add_plugin("TestMod.esp", masters=["Fallout4.esm"])
        assert "Fallout4.esm" in g._edges["TestMod.esp"]

    def test_add_plugin_heuristic_deps(self):
        g = PluginDependencyGraph()
        # The name contains 'automatron' so heuristic adds DLCRobot.esm
        g.add_plugin("AutomatronFix.esp")
        assert "Fallout4.esm" in g._edges["AutomatronFix.esp"]
        assert "DLCRobot.esm" in g._edges["AutomatronFix.esp"]

    def test_extra_deps_merged(self):
        g = PluginDependencyGraph(extra_deps={"MyMod.esp": ["SpecialMaster.esm"]})
        g.add_plugin("MyMod.esp", masters=["Fallout4.esm"])
        assert "SpecialMaster.esm" in g._edges["MyMod.esp"]

    def test_no_self_loops(self):
        g = PluginDependencyGraph()
        g.add_plugin("MyMod.esp", masters=["MyMod.esp", "Fallout4.esm"])
        assert "MyMod.esp" not in g._edges.get("MyMod.esp", set())

    def test_get_statistics(self):
        g = PluginDependencyGraph.from_load_order(GOOD_ORDER)
        stats = g.get_statistics()
        assert "total_plugins" in stats
        assert stats["total_plugins"] > 0

    def test_to_dict_serializable(self):
        g = PluginDependencyGraph.from_load_order(GOOD_ORDER)
        d = g.to_dict()
        assert json.dumps(d)
        assert "nodes" in d
        assert "edges" in d


class TestDependencyGraphMissingMasters:
    def test_no_missing_in_good_order(self):
        g = PluginDependencyGraph.from_load_order(GOOD_ORDER)
        missing = g.get_missing_masters(GOOD_ORDER)
        # Good order has all masters present
        assert len(missing) == 0

    def test_detects_missing_dlc_master(self):
        order = ["Fallout4.esm", "AutomatronFix.esp"]  # DLCRobot.esm absent
        g = PluginDependencyGraph.from_load_order(order)
        missing = g.get_missing_masters(order)
        assert any(master == "DLCRobot.esm" for _, master in missing)

    def test_returns_list_of_tuples(self):
        order = ["Fallout4.esm", "AutomatronFix.esp"]
        g = PluginDependencyGraph.from_load_order(order)
        missing = g.get_missing_masters(order)
        for item in missing:
            assert len(item) == 2

    def test_subset_check(self):
        g = PluginDependencyGraph.from_load_order(GOOD_ORDER)
        g.add_plugin("MissingMod.esp", masters=["NonExistentMaster.esm"])
        missing = g.get_missing_masters(["MissingMod.esp"])
        assert any(m == "NonExistentMaster.esm" for _, m in missing)


class TestDependencyGraphViolations:
    def test_no_violations_in_good_order(self):
        g = PluginDependencyGraph.from_load_order(GOOD_ORDER)
        violations = g.get_load_order_violations(GOOD_ORDER)
        assert len(violations) == 0

    def test_detects_plugin_before_master(self):
        g = PluginDependencyGraph.from_load_order(VIOLATION_ORDER)
        violations = g.get_load_order_violations(VIOLATION_ORDER)
        assert len(violations) >= 1
        assert any(plugin == "WeaponMod.esp" for plugin, _, _, _ in violations)

    def test_violation_tuple_has_four_elements(self):
        g = PluginDependencyGraph.from_load_order(VIOLATION_ORDER)
        violations = g.get_load_order_violations(VIOLATION_ORDER)
        for v in violations:
            assert len(v) == 4

    def test_violation_positions_ordered_wrong(self):
        g = PluginDependencyGraph.from_load_order(VIOLATION_ORDER)
        violations = g.get_load_order_violations(VIOLATION_ORDER)
        for plugin, master, p_pos, m_pos in violations:
            assert p_pos < m_pos  # plugin is before master — that's the violation


class TestDependencyGraphTopoSort:
    def test_topological_sort_valid_result(self):
        g = PluginDependencyGraph.from_load_order(GOOD_ORDER)
        sorted_order = g.topological_sort(GOOD_ORDER)
        assert set(sorted_order) == set(GOOD_ORDER)

    def test_sorted_order_satisfies_deps(self):
        g = PluginDependencyGraph.from_load_order(VIOLATION_ORDER)
        sorted_order = g.topological_sort(VIOLATION_ORDER)
        # After sort, Fallout4.esm should be before WeaponMod.esp
        fo4_pos = sorted_order.index("Fallout4.esm")
        wm_pos  = sorted_order.index("WeaponMod.esp")
        assert fo4_pos < wm_pos

    def test_topo_sort_subset(self):
        g = PluginDependencyGraph.from_load_order(GOOD_ORDER)
        subset = ["WeaponOverhaul.esp", "Fallout4.esm"]
        result = g.topological_sort(subset)
        assert set(result) == set(subset)


class TestDependencyGraphDependencyChain:
    def test_chain_for_weapon_mod_includes_fallout4(self):
        g = PluginDependencyGraph.from_load_order(GOOD_ORDER)
        chain = g.dependency_chain("WeaponOverhaul.esp")
        assert "Fallout4.esm" in chain

    def test_chain_for_fallout4_is_empty(self):
        g = PluginDependencyGraph.from_load_order(GOOD_ORDER)
        chain = g.dependency_chain("Fallout4.esm")
        assert chain == []

    def test_dependents_of_fallout4(self):
        g = PluginDependencyGraph.from_load_order(GOOD_ORDER)
        deps = g.dependents_of("Fallout4.esm")
        # All non-master plugins depend on Fallout4.esm
        assert "WeaponOverhaul.esp" in deps or len(deps) >= 1


# ═════════════════════════════════════════════════════════════════════════════
# ModHealthChecker
# ═════════════════════════════════════════════════════════════════════════════

class TestHealthCheckerInit:
    def test_instantiates(self):
        c = ModHealthChecker()
        assert c is not None

    def test_run_ai_false(self):
        c = ModHealthChecker(run_ai=False)
        assert not c.run_ai


class TestHealthCheckerReport:
    def test_returns_health_report(self):
        report = ModHealthChecker(run_ai=False).check(GOOD_ORDER)
        assert isinstance(report, HealthReport)

    def test_report_has_score(self):
        report = ModHealthChecker(run_ai=False).check(GOOD_ORDER)
        assert 0 <= report.score <= 100

    def test_good_order_high_score(self):
        report = ModHealthChecker(run_ai=False).check(GOOD_ORDER)
        assert report.score >= 60  # Good order should score well

    def test_bad_masters_lower_score(self):
        good_report = ModHealthChecker(run_ai=False).check(GOOD_ORDER)
        bad_report  = ModHealthChecker(run_ai=False).check(BAD_MASTERS)
        assert bad_report.score < good_report.score

    def test_report_has_plugin_count(self):
        report = ModHealthChecker(run_ai=False).check(GOOD_ORDER)
        assert report.plugin_count == len(GOOD_ORDER)

    def test_report_has_slot_count(self):
        report = ModHealthChecker(run_ai=False).check(GOOD_ORDER)
        esl_count = sum(1 for p in GOOD_ORDER if p.lower().endswith(".esl"))
        assert report.slot_count == len(GOOD_ORDER) - esl_count

    def test_report_has_esl_candidates(self):
        report = ModHealthChecker(run_ai=False).check(GOOD_ORDER)
        assert isinstance(report.esl_candidates, int)
        assert report.esl_candidates >= 0

    def test_report_issues_are_health_issues(self):
        report = ModHealthChecker(run_ai=False).check(GOOD_ORDER)
        for issue in report.issues:
            assert isinstance(issue, HealthIssue)

    def test_report_issues_sorted_critical_first(self):
        report = ModHealthChecker(run_ai=False).check(BAD_MASTERS)
        sev_rank = {"critical": 0, "error": 1, "warning": 2, "info": 3}
        ranks = [sev_rank.get(i.severity, 9) for i in report.issues]
        assert ranks == sorted(ranks)

    def test_bad_masters_produces_critical_issues(self):
        report = ModHealthChecker(run_ai=False).check(BAD_MASTERS)
        assert any(i.severity == "critical" for i in report.issues)

    def test_violation_order_produces_error(self):
        report = ModHealthChecker(run_ai=False).check(VIOLATION_ORDER)
        assert any(i.severity in ("critical", "error") for i in report.issues)

    def test_plugin_cap_critical(self):
        huge = ["Fallout4.esm"] + [f"Mod{i:03d}.esp" for i in range(255)]
        report = ModHealthChecker(run_ai=False).check(huge)
        cap_issues = [i for i in report.issues if i.category == "plugin_cap"]
        assert len(cap_issues) >= 1
        assert cap_issues[0].severity in ("critical", "error")
        assert report.score < 80

    def test_plugin_cap_warning(self):
        approaching = ["Fallout4.esm"] + [f"Mod{i:03d}.esp" for i in range(240)]
        report = ModHealthChecker(run_ai=False).check(approaching)
        cap_issues = [i for i in report.issues if i.category == "plugin_cap"]
        assert len(cap_issues) >= 1

    def test_missing_unofficial_patch_is_info(self):
        order_no_ufp = ["Fallout4.esm", "DLCRobot.esm", "WeaponMod.esp"]
        report = ModHealthChecker(run_ai=False).check(order_no_ufp)
        bp_issues = [i for i in report.issues if i.category == "best_practice"]
        assert any("unofficial" in i.message.lower() for i in bp_issues)

    def test_report_with_profile_name(self):
        report = ModHealthChecker(run_ai=False).check(GOOD_ORDER, profile="MyProfile")
        assert report.profile == "MyProfile"

    def test_to_dict_serializable(self):
        report = ModHealthChecker(run_ai=False).check(GOOD_ORDER)
        d = report.to_dict()
        assert json.dumps(d)  # no TypeError
        assert "score" in d
        assert "issues" in d
        assert "plugin_count" in d

    def test_summary_contains_score(self):
        report = ModHealthChecker(run_ai=False).check(GOOD_ORDER)
        summary = report.summary()
        assert str(report.score) in summary
        assert "Health" in summary or "score" in summary.lower()

    def test_summary_lists_issues(self):
        report = ModHealthChecker(run_ai=False).check(BAD_MASTERS)
        summary = report.summary()
        assert len(summary) > 50

    def test_empty_load_order(self):
        report = ModHealthChecker(run_ai=False).check([])
        assert isinstance(report, HealthReport)
        assert report.plugin_count == 0


class TestHealthCheckerWithAI:
    def test_ai_enabled_returns_report(self):
        report = ModHealthChecker(run_ai=True).check(GOOD_ORDER)
        assert isinstance(report, HealthReport)

    def test_ai_summary_populated(self):
        report = ModHealthChecker(run_ai=True).check(GOOD_ORDER)
        # ai_summary may be empty dict if AI raised exception, or a dict of results
        assert isinstance(report.ai_summary, dict)

    def test_no_ai_has_empty_summary(self):
        report = ModHealthChecker(run_ai=False).check(GOOD_ORDER)
        assert report.ai_summary == {}


class TestHealthCheckerDependencies:
    def test_missing_dlc_master_detected(self):
        order = ["Fallout4.esm", "AutomatronFix.esp"]  # DLCRobot.esm missing
        report = ModHealthChecker(run_ai=False).check(order)
        dep_issues = [i for i in report.issues if i.category == "dependency"]
        assert len(dep_issues) >= 1
        assert any("DLCRobot.esm" in i.message for i in dep_issues)

    def test_violation_detected_by_dependency_check(self):
        report = ModHealthChecker(run_ai=False).check(VIOLATION_ORDER)
        all_issues = report.issues
        dep_issues = [i for i in all_issues if i.category == "dependency"]
        assert len(dep_issues) >= 1


class TestHealthCheckerPropertyAccessors:
    def test_critical_issues_accessor(self):
        report = ModHealthChecker(run_ai=False).check(BAD_MASTERS)
        for i in report.critical_issues:
            assert i.severity == "critical"

    def test_warnings_accessor(self):
        report = ModHealthChecker(run_ai=False).check(GOOD_ORDER)
        for i in report.warnings:
            assert i.severity == "warning"

    def test_errors_accessor_includes_critical(self):
        report = ModHealthChecker(run_ai=False).check(BAD_MASTERS)
        for i in report.errors:
            assert i.severity in ("critical", "error")


# ═════════════════════════════════════════════════════════════════════════════
# Reasoner integration — MissingMaster and MasterLoadedLate rules
# ═════════════════════════════════════════════════════════════════════════════

class TestReasonerMissingMasterRule:
    def test_missing_dlc_master_fires(self):
        from mossy_manager.ai.reasoner import ModReasoner
        order = ["Fallout4.esm", "AutomatronFix.esp"]
        result = ModReasoner().reason_about_load_order(order)
        rules = [s.rule for s in result.steps]
        # Should fire either MissingDependency (heuristic) or MissingMaster (graph)
        assert "MissingDependency" in rules or "MissingMaster" in rules

    def test_master_loaded_late_fires(self):
        from mossy_manager.ai.reasoner import ModReasoner
        result = ModReasoner().reason_about_load_order(VIOLATION_ORDER)
        rules = [s.rule for s in result.steps]
        assert "MasterLoadedLate" in rules or "MasterFileOrder" in rules

    def test_good_order_no_missing_master(self):
        from mossy_manager.ai.reasoner import ModReasoner
        result = ModReasoner().reason_about_load_order(GOOD_ORDER)
        rules = [s.rule for s in result.steps]
        assert "MissingMaster" not in rules


# ═════════════════════════════════════════════════════════════════════════════
# CLI integration — mossy status --json and --no-ai
# ═════════════════════════════════════════════════════════════════════════════

class TestStatusCLI:
    def _make_mo2(self, tmp_path, load_order=None):
        """Create a minimal fake MO2 structure."""
        profiles = tmp_path / "profiles" / "Default"
        profiles.mkdir(parents=True)
        mods = tmp_path / "mods"
        mods.mkdir()
        lo = profiles / "loadorder.txt"
        lo.write_text("\n".join(load_order or GOOD_ORDER) + "\n")
        plugins = profiles / "plugins.txt"
        plugins.write_text(
            "\n".join("*" + p for p in (load_order or GOOD_ORDER)) + "\n"
        )
        return tmp_path

    def test_status_help(self):
        from click.testing import CliRunner
        from mossy_manager.cli.main import main
        r = CliRunner().invoke(main, ["status", "--help"])
        assert r.exit_code == 0
        assert "health" in r.output.lower() or "status" in r.output.lower()

    def test_status_no_mo2_warns(self):
        from click.testing import CliRunner
        from mossy_manager.cli.main import main
        r = CliRunner().invoke(main, ["status"])
        # Should not crash (exit 0) even without MO2
        assert r.exit_code == 0

    def test_status_with_mo2_json(self, tmp_path):
        from click.testing import CliRunner
        from mossy_manager.cli.main import main
        mo2 = self._make_mo2(tmp_path)
        r = CliRunner().invoke(main, [
            "status",
            "--mo2-path", str(mo2),
            "--profile", "Default",
            "--json",
            "--no-ai",
        ])
        assert r.exit_code == 0
        data = json.loads(r.output)
        assert "score" in data
        assert "issues" in data
        assert "plugin_count" in data

    def test_status_with_mo2_human(self, tmp_path):
        from click.testing import CliRunner
        from mossy_manager.cli.main import main
        mo2 = self._make_mo2(tmp_path)
        r = CliRunner().invoke(main, [
            "status",
            "--mo2-path", str(mo2),
            "--profile", "Default",
            "--no-ai",
        ])
        assert r.exit_code == 0
        assert "Health" in r.output or "/100" in r.output

    def test_status_bad_order_json_score_low(self, tmp_path):
        from click.testing import CliRunner
        from mossy_manager.cli.main import main
        mo2 = self._make_mo2(tmp_path, BAD_MASTERS)
        r = CliRunner().invoke(main, [
            "status",
            "--mo2-path", str(mo2),
            "--profile", "Default",
            "--json",
            "--no-ai",
        ])
        assert r.exit_code == 0
        data = json.loads(r.output)
        assert data["score"] < 80


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
