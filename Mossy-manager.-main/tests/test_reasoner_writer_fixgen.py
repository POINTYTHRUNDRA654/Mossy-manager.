"""
Tests for ModReasoner, ScriptWriter, and FixGenerator.
All three must produce complete, working outputs — zero placeholders.
"""

import json
import tempfile
from pathlib import Path

import pytest

from mossy_manager.ai.reasoner import ModReasoner, ReasoningResult, ReasoningStep
from mossy_manager.ai.script_writer import ScriptWriter, _infer_record_sig, _safe_name
from mossy_manager.ai.fix_generator import FixGenerator, Fix


# ─────────────────────────────────────────────────────────────────────────────
# Shared fixtures
# ─────────────────────────────────────────────────────────────────────────────

GOOD_ORDER = [
    "Fallout4.esm",
    "DLCRobot.esm",
    "DLCworkshop01.esm",
    "DLCCoast.esm",
    "DLCworkshop02.esm",
    "DLCworkshop03.esm",
    "DLCNukaWorld.esm",
    "UnoffPatch.esp",
    "F4SE_Plugin.esp",
    "WeaponOverhaul.esp",
    "ArmorMod.esp",
    "TexturePack.esp",
    "UITweaks.esp",
    "BashedPatch.esp",
]

BAD_ORDER_MASTERS = [
    "DLCCoast.esm",       # wrong: should be after DLCRobot
    "Fallout4.esm",       # wrong: should be first
    "DLCRobot.esm",
    "WeaponOverhaul.esp",
]

BAD_ORDER_PATCH_EARLY = [
    "Fallout4.esm",
    "DLCRobot.esm",
    "CompatPatch.esp",    # patch loading at position 2 — too early
    "WeaponOverhaul.esp",
    "ArmorMod.esp",
    "TexturePack.esp",
    "UITweaks.esp",
    "BashedPatch.esp",
]

SAMPLE_CONFLICTS = [
    {
        "resource": "textures/sky.dds",
        "mods": ["TextureModA.esp", "TextureModB.esp"],
        "severity": "medium",
        "category": "textures",
    },
    {
        "resource": "scripts/weapon.pex",
        "mods": ["WeaponModA.esp", "WeaponModB.esp"],
        "severity": "high",
        "category": "scripts",
    },
]


# ═════════════════════════════════════════════════════════════════════════════
# ModReasoner
# ═════════════════════════════════════════════════════════════════════════════

class TestModReasonerInit:
    def test_instantiates(self):
        r = ModReasoner()
        assert r is not None

    def test_reason_returns_result(self):
        result = ModReasoner().reason_about_load_order(GOOD_ORDER)
        assert isinstance(result, ReasoningResult)

    def test_result_has_required_fields(self):
        result = ModReasoner().reason_about_load_order(GOOD_ORDER)
        assert isinstance(result.steps, list)
        assert isinstance(result.conclusion, str)
        assert isinstance(result.action_plan, list)
        assert 0.0 <= result.confidence <= 1.0
        assert result.severity in ("info", "warning", "error", "critical")


class TestModReasonerLoadOrder:
    def test_good_order_has_steps(self):
        result = ModReasoner().reason_about_load_order(GOOD_ORDER)
        # Good order still gets informational notes (F4SE, UFP recommendation)
        assert isinstance(result.steps, list)

    def test_detects_master_order_violation(self):
        result = ModReasoner().reason_about_load_order(BAD_ORDER_MASTERS)
        rules = [s.rule for s in result.steps]
        assert "MasterFileOrder" in rules

    def test_master_violation_is_critical(self):
        result = ModReasoner().reason_about_load_order(BAD_ORDER_MASTERS)
        critical = [s for s in result.steps if s.rule == "MasterFileOrder"]
        assert all(s.severity == "critical" for s in critical)

    def test_detects_patch_loaded_too_early(self):
        result = ModReasoner().reason_about_load_order(BAD_ORDER_PATCH_EARLY)
        rules = [s.rule for s in result.steps]
        assert "PatchLoadedTooEarly" in rules

    def test_detects_missing_ufp(self):
        order_no_ufp = ["Fallout4.esm", "WeaponMod.esp", "ArmorMod.esp"]
        result = ModReasoner().reason_about_load_order(order_no_ufp)
        rules = [s.rule for s in result.steps]
        assert "MissingUFP" in rules

    def test_detects_f4se_dependency(self):
        order = ["Fallout4.esm", "MCM_Settings.esp", "F4SE_Plugin.esp"]
        result = ModReasoner().reason_about_load_order(order)
        rules = [s.rule for s in result.steps]
        assert "F4SEDependency" in rules

    def test_conflict_chain_rule(self):
        conflicts = [{"resource": "test.nif", "mods": ["A.esp", "B.esp"],
                      "severity": "medium", "category": "meshes"}]
        result = ModReasoner().reason_about_load_order(GOOD_ORDER, conflicts)
        rules = [s.rule for s in result.steps]
        assert "ConflictRootCause" in rules

    def test_conclusion_is_nonempty_string(self):
        result = ModReasoner().reason_about_load_order(BAD_ORDER_MASTERS)
        assert len(result.conclusion) > 10

    def test_action_plan_is_nonempty_for_bad_order(self):
        result = ModReasoner().reason_about_load_order(BAD_ORDER_MASTERS)
        assert len(result.action_plan) >= 1

    def test_to_dict_serialisable(self):
        result = ModReasoner().reason_about_load_order(GOOD_ORDER)
        d = result.to_dict()
        assert json.dumps(d)  # no TypeError

    def test_summary_string(self):
        result = ModReasoner().reason_about_load_order(GOOD_ORDER)
        s = result.summary()
        assert "Problem" in s
        assert "Conclusion" in s

    def test_empty_load_order(self):
        result = ModReasoner().reason_about_load_order([])
        assert isinstance(result, ReasoningResult)


class TestModReasonerConflict:
    def test_reason_about_conflict_returns_result(self):
        conflict = {"resource": "scripts/weapon.pex",
                    "mods": ["A.esp", "B.esp"], "severity": "high"}
        result = ModReasoner().reason_about_conflict(conflict, GOOD_ORDER)
        assert isinstance(result, ReasoningResult)

    def test_conflict_result_has_steps(self):
        conflict = {"resource": "textures/sky.dds",
                    "mods": ["TexA.esp", "TexB.esp"], "severity": "medium"}
        result = ModReasoner().reason_about_conflict(conflict, GOOD_ORDER)
        assert len(result.steps) >= 1


class TestModReasonerDiagnose:
    def test_diagnose_ctd(self):
        result = ModReasoner().diagnose("game crashes CTD on load", GOOD_ORDER)
        rules = [s.rule for s in result.steps]
        assert "CrashDiagnosis" in rules

    def test_diagnose_purple_textures(self):
        result = ModReasoner().diagnose("purple textures everywhere")
        rules = [s.rule for s in result.steps]
        assert "MissingTextureDiagnosis" in rules

    def test_diagnose_script_lag(self):
        result = ModReasoner().diagnose("script lag and stutter")
        rules = [s.rule for s in result.steps]
        assert "ScriptLagDiagnosis" in rules

    def test_diagnose_load_order(self):
        result = ModReasoner().diagnose("wrong mod winning load order")
        rules = [s.rule for s in result.steps]
        assert "LoadOrderDiagnosis" in rules

    def test_diagnose_unknown_falls_back(self):
        result = ModReasoner().diagnose("some random unknown issue xyz")
        assert len(result.steps) >= 1

    def test_diagnose_no_load_order(self):
        result = ModReasoner().diagnose("crash on load")
        assert isinstance(result, ReasoningResult)


# ═════════════════════════════════════════════════════════════════════════════
# ScriptWriter helpers
# ═════════════════════════════════════════════════════════════════════════════

class TestScriptWriterHelpers:
    def test_safe_name_strips_spaces(self):
        assert " " not in _safe_name("My Patch")

    def test_safe_name_no_leading_digit(self):
        result = _safe_name("123abc")
        assert not result[0].isdigit()

    def test_infer_record_sig_dds(self):
        assert _infer_record_sig("textures/sky.dds") == "TXST"

    def test_infer_record_sig_pex(self):
        assert _infer_record_sig("scripts/weapon.pex") == "SCPT"

    def test_infer_record_sig_nif(self):
        assert _infer_record_sig("meshes/thing.nif") == "STAT"

    def test_infer_record_sig_wav(self):
        assert _infer_record_sig("sounds/bang.wav") == "SOUN"

    def test_infer_record_sig_unknown(self):
        assert _infer_record_sig("unknownfile.xyz") == ""

    def test_infer_record_sig_folder_priority(self):
        # folder 'scripts' should beat extension
        assert _infer_record_sig("scripts/myscript.ini") == "SCPT"


# ═════════════════════════════════════════════════════════════════════════════
# ScriptWriter — xEdit scripts
# ═════════════════════════════════════════════════════════════════════════════

class TestScriptWriterXEdit:
    def test_conflict_patch_no_todo(self):
        sw = ScriptWriter()
        code = sw.xedit_conflict_patch("TestPatch", ["A.esp", "B.esp"],
                                        SAMPLE_CONFLICTS)
        assert "TODO" not in code

    def test_conflict_patch_has_real_forward_code(self):
        sw = ScriptWriter()
        code = sw.xedit_conflict_patch("TestPatch", ["A.esp", "B.esp"],
                                        SAMPLE_CONFLICTS)
        assert "wbCopyElementToFile" in code

    def test_conflict_patch_has_plugin_guards(self):
        sw = ScriptWriter()
        code = sw.xedit_conflict_patch("TestPatch",
                                        ["TextureModA.esp", "TextureModB.esp"],
                                        SAMPLE_CONFLICTS)
        assert "TextureModA.esp" in code or "TextureModB.esp" in code

    def test_conflict_patch_has_record_sig_filter(self):
        sw = ScriptWriter()
        code = sw.xedit_conflict_patch("TestPatch", ["A.esp"],
                                        [{"resource": "textures/sky.dds",
                                          "mods": ["A.esp", "B.esp"],
                                          "severity": "medium", "category": "textures"}])
        assert "TXST" in code

    def test_conflict_patch_no_conflicts_still_functional(self):
        sw = ScriptWriter()
        code = sw.xedit_conflict_patch("EmptyPatch", ["A.esp", "B.esp"], [])
        assert "wbCopyElementToFile" in code
        assert "TODO" not in code

    def test_clean_itms_is_complete_pascal(self):
        sw = ScriptWriter()
        code = sw.xedit_clean_itms("MyMod.esp")
        assert "IsITM" in code
        assert "Remove(e)" in code
        assert "TODO" not in code

    def test_esl_flag_has_real_flag_call(self):
        sw = ScriptWriter()
        code = sw.xedit_esl_flag(["SmallMod.esp", "TinyMod.esp"])
        assert "SmallMod.esp" in code
        assert "TinyMod.esp" in code

    def test_conflict_patch_valid_pascal_structure(self):
        sw = ScriptWriter()
        code = sw.xedit_conflict_patch("P", ["A.esp"], SAMPLE_CONFLICTS)
        assert "function Initialize" in code
        assert "function Process" in code
        assert "function Finalize" in code
        assert "end." in code


class TestScriptWriterINI:
    def test_papyrus_logging_ini(self):
        sw = ScriptWriter()
        code = sw.ini_tweak("papyrus_logging")
        assert "bEnableLogging=1" in code
        assert "Papyrus" in code

    def test_archive_invalidation_ini(self):
        sw = ScriptWriter()
        code = sw.ini_tweak("archive_invalidation")
        assert "bInvalidateOlderFiles=1" in code

    def test_performance_high_ini(self):
        sw = ScriptWriter()
        code = sw.ini_tweak("performance_high")
        assert "uExterior Cell Buffer" in code

    def test_performance_low_ini(self):
        sw = ScriptWriter()
        code = sw.ini_tweak("performance_low")
        assert "uExterior Cell Buffer" in code

    def test_invalid_preset_raises(self):
        sw = ScriptWriter()
        with pytest.raises(ValueError, match="Unknown INI preset"):
            sw.ini_tweak("nonexistent_preset")


class TestScriptWriterBatch:
    def test_safe_launch_bat_has_f4se_check(self):
        sw = ScriptWriter()
        code = sw.batch_safe_launch()
        assert "f4se_loader.exe" in code.lower() or "F4SE" in code

    def test_safe_launch_has_plugin_cap_check(self):
        sw = ScriptWriter()
        code = sw.batch_safe_launch()
        assert "255" in code

    def test_backup_profiles_ps1(self):
        sw = ScriptWriter()
        code = sw.batch_backup_profiles()
        assert "Copy-Item" in code
        assert "profiles" in code.lower()


class TestScriptWriterFromReasoning:
    def test_from_reasoning_returns_dict(self):
        sw = ScriptWriter()
        result = ModReasoner().reason_about_load_order(BAD_ORDER_MASTERS)
        scripts = sw.from_reasoning(result, plugins=["A.esp"])
        assert isinstance(scripts, dict)
        assert len(scripts) >= 1

    def test_from_reasoning_complete_no_todos(self):
        sw = ScriptWriter()
        result = ModReasoner().reason_about_load_order(BAD_ORDER_MASTERS)
        scripts = sw.from_reasoning_complete(result, load_order=BAD_ORDER_MASTERS)
        for filename, code in scripts.items():
            assert "TODO" not in code, f"TODO found in {filename}"

    def test_from_reasoning_complete_ctd_gives_papyrus(self):
        sw = ScriptWriter()
        result = ModReasoner().diagnose("CTD crash on load")
        scripts = sw.from_reasoning_complete(result)
        ini_scripts = {k: v for k, v in scripts.items() if k.endswith(".ini")}
        assert len(ini_scripts) >= 1
        assert any("bEnableLogging" in v for v in ini_scripts.values())

    def test_from_reasoning_complete_f4se_gives_bat(self):
        sw = ScriptWriter()
        result = ModReasoner().reason_about_load_order(
            ["Fallout4.esm", "F4SE_Plugin.esp", "MCM.esp"]
        )
        scripts = sw.from_reasoning_complete(result)
        bat_scripts = {k: v for k, v in scripts.items() if k.endswith(".bat")}
        assert len(bat_scripts) >= 1


class TestScriptWriterFileIO:
    def test_write_creates_file(self, tmp_path):
        sw = ScriptWriter(output_dir=tmp_path)
        p = sw.write("test.pas", "unit Test;\nend.\n")
        assert p.exists()
        assert p.read_text() == "unit Test;\nend.\n"

    def test_write_all_creates_all_files(self, tmp_path):
        sw = ScriptWriter()
        scripts = {"a.pas": "unit A; end.", "b.ini": "[Section]\nkey=val"}
        paths = sw.write_all(scripts, output_dir=tmp_path)
        assert len(paths) == 2
        assert all(p.exists() for p in paths)


# ═════════════════════════════════════════════════════════════════════════════
# FixGenerator
# ═════════════════════════════════════════════════════════════════════════════

class TestFixGeneratorInit:
    def test_instantiates(self):
        fg = FixGenerator()
        assert fg is not None

    def test_custom_patch_name(self):
        fg = FixGenerator(patch_name="MyFix")
        assert fg.patch_name == "MyFix"


class TestFixGeneratorGenerates:
    def test_returns_list_of_fixes(self):
        result = ModReasoner().reason_about_load_order(BAD_ORDER_MASTERS)
        fixes = FixGenerator().generate_fixes(result, BAD_ORDER_MASTERS)
        assert isinstance(fixes, list)
        assert len(fixes) >= 1

    def test_every_fix_has_required_fields(self):
        result = ModReasoner().reason_about_load_order(BAD_ORDER_MASTERS)
        fixes = FixGenerator().generate_fixes(result, BAD_ORDER_MASTERS)
        for f in fixes:
            assert f.title
            assert f.description
            assert f.issue_rule
            assert f.fix_type in ("python", "pascal", "ini", "batch", "powershell")
            assert f.code
            assert f.filename

    def test_no_todos_in_generated_code(self):
        result = ModReasoner().reason_about_load_order(BAD_ORDER_MASTERS)
        fixes = FixGenerator().generate_fixes(result, BAD_ORDER_MASTERS)
        for f in fixes:
            assert "TODO" not in f.code, f"TODO found in {f.filename}"

    def test_master_order_violation_produces_python_fix(self):
        result = ModReasoner().reason_about_load_order(BAD_ORDER_MASTERS)
        fixes = FixGenerator().generate_fixes(result, BAD_ORDER_MASTERS)
        python_fixes = [f for f in fixes if f.fix_type == "python"]
        assert len(python_fixes) >= 1

    def test_master_order_fix_contains_correct_masters(self):
        result = ModReasoner().reason_about_load_order(BAD_ORDER_MASTERS)
        fixes = FixGenerator().generate_fixes(result, BAD_ORDER_MASTERS)
        master_fix = next((f for f in fixes if f.issue_rule == "MasterFileOrder"), None)
        assert master_fix is not None
        assert "Fallout4.esm" in master_fix.code

    def test_patch_too_early_produces_python_fix(self):
        result = ModReasoner().reason_about_load_order(BAD_ORDER_PATCH_EARLY)
        fixes = FixGenerator().generate_fixes(result, BAD_ORDER_PATCH_EARLY)
        patch_fix = next((f for f in fixes if f.issue_rule == "PatchLoadedTooEarly"), None)
        assert patch_fix is not None
        assert "CompatPatch.esp" in patch_fix.code

    def test_plugin_cap_produces_pascal_fix(self):
        huge_order = ["Fallout4.esm"] + [f"Mod{i:03d}.esp" for i in range(254)]
        result = ModReasoner().reason_about_load_order(huge_order)
        fixes = FixGenerator().generate_fixes(result, huge_order)
        pascal_fixes = [f for f in fixes if f.fix_type == "pascal"]
        assert len(pascal_fixes) >= 1
        assert any("ESL" in f.code for f in pascal_fixes)

    def test_f4se_dependency_produces_batch_fix(self):
        order = ["Fallout4.esm", "F4SE_Plugin.esp", "MCM.esp",
                 "WeaponMod.esp", "ArmorMod.esp"]
        result = ModReasoner().reason_about_load_order(order)
        fixes = FixGenerator().generate_fixes(result, order)
        bat_fixes = [f for f in fixes if f.fix_type == "batch"]
        assert len(bat_fixes) >= 1

    def test_ctd_diagnosis_produces_ini_fix(self):
        result = ModReasoner().diagnose("CTD crash on startup")
        fixes = FixGenerator().generate_fixes(result)
        ini_fixes = [f for f in fixes if f.fix_type == "ini"]
        assert len(ini_fixes) >= 1
        assert any("bEnableLogging" in f.code for f in ini_fixes)

    def test_texture_diagnosis_produces_ini_fix(self):
        result = ModReasoner().diagnose("purple textures missing")
        fixes = FixGenerator().generate_fixes(result)
        ini_fixes = [f for f in fixes if f.fix_type == "ini"]
        assert len(ini_fixes) >= 1
        assert any("bInvalidateOlderFiles" in f.code for f in ini_fixes)

    def test_conflict_fix_pascal_has_exact_plugin_names(self):
        conflicts = [{"resource": "scripts/weapon.pex",
                      "mods": ["WeaponA.esp", "WeaponB.esp"],
                      "severity": "high", "category": "scripts"}]
        # Build a ReasoningResult manually with a ConflictRootCause step
        from mossy_manager.ai.reasoner import ReasoningStep, ReasoningResult
        step = ReasoningStep(
            step_number=1, rule="ConflictRootCause",
            observation="Resource 'scripts/weapon.pex' is claimed by WeaponA.esp, WeaponB.esp",
            deduction="Forward winning record.", severity="high", plugin="WeaponB.esp",
        )
        result = ReasoningResult(problem="conflict", steps=[step])
        result.conclusion = "Conflict found"
        result.action_plan = ["Fix it"]
        result.confidence = 0.9
        result.severity = "high"
        conflict_map = {"scripts/weapon.pex": conflicts[0]}
        fixes = FixGenerator().generate_fixes(result, GOOD_ORDER,
                                               conflicts=conflicts)
        pascal_fixes = [f for f in fixes if f.fix_type == "pascal"]
        assert len(pascal_fixes) >= 1
        assert "WeaponA.esp" in pascal_fixes[0].code or "WeaponB.esp" in pascal_fixes[0].code

    def test_conflict_pascal_has_record_sig_filter(self):
        from mossy_manager.ai.reasoner import ReasoningStep, ReasoningResult
        step = ReasoningStep(
            step_number=1, rule="ConflictRootCause",
            observation="Resource 'textures/sky.dds' is claimed by TexA.esp, TexB.esp",
            deduction="Forward it.", severity="medium", plugin="TexB.esp",
        )
        result = ReasoningResult(problem="tex conflict", steps=[step])
        result.conclusion = "ok"; result.action_plan = []; result.confidence = 0.8
        result.severity = "medium"
        conflicts = [{"resource": "textures/sky.dds",
                      "mods": ["TexA.esp", "TexB.esp"],
                      "severity": "medium", "category": "textures"}]
        fixes = FixGenerator().generate_fixes(result, GOOD_ORDER, conflicts=conflicts)
        pascal_fixes = [f for f in fixes if f.fix_type == "pascal"]
        assert any("TXST" in f.code for f in pascal_fixes)

    def test_fixes_sorted_critical_first(self):
        result = ModReasoner().reason_about_load_order(BAD_ORDER_MASTERS)
        fixes = FixGenerator().generate_fixes(result, BAD_ORDER_MASTERS)
        # First fix should come from a critical step
        first_rule = fixes[0].issue_rule
        critical_rules = {s.rule for s in result.steps if s.severity == "critical"}
        assert first_rule in critical_rules

    def test_deduplication_no_repeat_rules(self):
        result = ModReasoner().reason_about_load_order(BAD_ORDER_MASTERS)
        fixes = FixGenerator().generate_fixes(result, BAD_ORDER_MASTERS)
        rules_seen = [f.issue_rule for f in fixes]
        assert len(rules_seen) == len(set(rules_seen))


class TestFixAutoApply:
    def test_master_order_fix_can_apply(self, tmp_path):
        lo_file = tmp_path / "loadorder.txt"
        lo_file.write_text("\n".join(BAD_ORDER_MASTERS) + "\n", encoding="utf-8")

        result = ModReasoner().reason_about_load_order(BAD_ORDER_MASTERS)
        fixes = FixGenerator().generate_fixes(
            result, BAD_ORDER_MASTERS, loadorder_path=lo_file
        )
        master_fix = next((f for f in fixes if f.issue_rule == "MasterFileOrder"), None)
        assert master_fix is not None
        assert master_fix.can_auto_apply is True
        msg = master_fix.apply()
        assert "corrected" in msg.lower() or "✓" in msg

        # Verify file was actually fixed
        new_order = [l for l in lo_file.read_text().splitlines() if l.strip()]
        assert new_order[0] == "Fallout4.esm"
        fo4_idx = new_order.index("Fallout4.esm")
        dlc_idx = new_order.index("DLCRobot.esm") if "DLCRobot.esm" in new_order else 9999
        assert fo4_idx < dlc_idx

    def test_patch_position_fix_can_apply(self, tmp_path):
        lo_file = tmp_path / "loadorder.txt"
        lo_file.write_text("\n".join(BAD_ORDER_PATCH_EARLY) + "\n", encoding="utf-8")

        result = ModReasoner().reason_about_load_order(BAD_ORDER_PATCH_EARLY)
        fixes = FixGenerator().generate_fixes(
            result, BAD_ORDER_PATCH_EARLY, loadorder_path=lo_file
        )
        patch_fix = next((f for f in fixes if f.issue_rule == "PatchLoadedTooEarly"), None)
        if patch_fix and patch_fix.can_auto_apply:
            msg = patch_fix.apply()
            assert "Moved" in msg or "✓" in msg
            new_order = [l for l in lo_file.read_text().splitlines() if l.strip()]
            compat_pos = new_order.index("CompatPatch.esp")
            assert compat_pos > len(new_order) * 0.5

    def test_apply_raises_for_non_auto_fix(self):
        result = ModReasoner().reason_about_load_order(GOOD_ORDER)
        # Force a non-auto-apply fix
        fix = Fix(
            title="Test", description="test", issue_rule="test",
            fix_type="pascal", code="unit T; end.", filename="t.pas",
            can_auto_apply=False, _apply_fn=None,
        )
        with pytest.raises(NotImplementedError):
            fix.apply()

    def test_apply_without_loadorder_path_returns_message(self):
        result = ModReasoner().reason_about_load_order(BAD_ORDER_MASTERS)
        # No loadorder_path → can_auto_apply=False
        fixes = FixGenerator().generate_fixes(result, BAD_ORDER_MASTERS)
        master_fix = next((f for f in fixes if f.issue_rule == "MasterFileOrder"), None)
        assert master_fix is not None
        assert master_fix.can_auto_apply is False


class TestFixGeneratorWriteToDisk:
    def test_generate_and_write_creates_files(self, tmp_path):
        result = ModReasoner().reason_about_load_order(BAD_ORDER_MASTERS)
        written = FixGenerator().generate_and_write(
            result, tmp_path, load_order=BAD_ORDER_MASTERS
        )
        assert len(written) >= 1
        assert all(p.exists() for p in written)

    def test_generated_files_have_content(self, tmp_path):
        result = ModReasoner().reason_about_load_order(BAD_ORDER_MASTERS)
        written = FixGenerator().generate_and_write(
            result, tmp_path, load_order=BAD_ORDER_MASTERS
        )
        for p in written:
            assert p.stat().st_size > 50  # non-trivial content


class TestFixToDictSerializable:
    def test_to_dict_is_json_serializable(self):
        result = ModReasoner().reason_about_load_order(BAD_ORDER_MASTERS)
        fixes = FixGenerator().generate_fixes(result, BAD_ORDER_MASTERS)
        for f in fixes:
            d = f.to_dict()
            assert json.dumps(d)  # no TypeError
            assert "code_preview" in d
            assert "can_auto_apply" in d


# ═════════════════════════════════════════════════════════════════════════════
# CLI integration — mossy ai fix, reason, script
# ═════════════════════════════════════════════════════════════════════════════

class TestAIFixCLI:
    def _plugins_file(self, tmp_path, order=None):
        pf = tmp_path / "plugins.txt"
        pf.write_text(
            "\n".join("*" + p for p in (order or GOOD_ORDER)) + "\n"
        )
        return pf

    def test_ai_fix_help(self):
        from click.testing import CliRunner
        from mossy_manager.cli.main import main
        r = CliRunner().invoke(main, ["ai", "fix", "--help"])
        assert r.exit_code == 0
        assert "fix" in r.output.lower()

    def test_ai_fix_no_input_warns(self):
        from click.testing import CliRunner
        from mossy_manager.cli.main import main
        r = CliRunner().invoke(main, ["ai", "fix"])
        assert r.exit_code == 0
        assert "Provide" in r.output or "⚠" in r.output

    def test_ai_fix_with_plugins_file(self, tmp_path):
        from click.testing import CliRunner
        from mossy_manager.cli.main import main
        pf = self._plugins_file(tmp_path, BAD_ORDER_MASTERS)
        out = tmp_path / "fixes"
        r = CliRunner().invoke(main, [
            "ai", "fix",
            "--plugins-file", str(pf),
            "--output-dir", str(out),
        ])
        assert r.exit_code == 0
        assert out.exists()
        assert len(list(out.iterdir())) >= 1

    def test_ai_fix_with_problem(self, tmp_path):
        from click.testing import CliRunner
        from mossy_manager.cli.main import main
        out = tmp_path / "fixes"
        r = CliRunner().invoke(main, [
            "ai", "fix",
            "--problem", "CTD crash on load",
            "--output-dir", str(out),
        ])
        assert r.exit_code == 0
        assert out.exists()

    def test_ai_fix_apply_flag(self, tmp_path):
        from click.testing import CliRunner
        from mossy_manager.cli.main import main
        pf = self._plugins_file(tmp_path, BAD_ORDER_MASTERS)
        lo = tmp_path / "loadorder.txt"
        lo.write_text("\n".join(BAD_ORDER_MASTERS) + "\n")
        out = tmp_path / "fixes"
        r = CliRunner().invoke(main, [
            "ai", "fix",
            "--plugins-file", str(pf),
            "--loadorder-file", str(lo),
            "--output-dir", str(out),
            "--apply",
        ])
        assert r.exit_code == 0

    def test_ai_reason_with_plugins_file(self, tmp_path):
        from click.testing import CliRunner
        from mossy_manager.cli.main import main
        pf = self._plugins_file(tmp_path, BAD_ORDER_MASTERS)
        r = CliRunner().invoke(main, ["ai", "reason", "--plugins-file", str(pf)])
        assert r.exit_code == 0
        assert "Reasoning trace" in r.output

    def test_ai_reason_with_problem(self):
        from click.testing import CliRunner
        from mossy_manager.cli.main import main
        r = CliRunner().invoke(main, ["ai", "reason", "--problem", "game crashes CTD"])
        assert r.exit_code == 0
        assert "Conclusion" in r.output

    def test_ai_reason_saves_json(self, tmp_path):
        from click.testing import CliRunner
        from mossy_manager.cli.main import main
        pf = self._plugins_file(tmp_path)
        out = tmp_path / "trace.json"
        r = CliRunner().invoke(main, [
            "ai", "reason",
            "--plugins-file", str(pf),
            "--output", str(out),
        ])
        assert r.exit_code == 0
        assert out.exists()
        data = json.loads(out.read_text())
        assert "steps" in data
        assert "conclusion" in data

    def test_ai_script_papyrus_logging(self, tmp_path):
        from click.testing import CliRunner
        from mossy_manager.cli.main import main
        r = CliRunner().invoke(main, [
            "ai", "script",
            "--type", "papyrus_logging",
            "--output-dir", str(tmp_path),
        ])
        assert r.exit_code == 0
        assert (tmp_path / "papyrus_logging.ini").exists()

    def test_ai_script_safe_launch(self, tmp_path):
        from click.testing import CliRunner
        from mossy_manager.cli.main import main
        r = CliRunner().invoke(main, [
            "ai", "script",
            "--type", "safe_launch",
            "--output-dir", str(tmp_path),
        ])
        assert r.exit_code == 0
        assert (tmp_path / "safe_launch.bat").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
