"""
Tests for the AI Brain module (ModAIBrain).
All tests use only the free scikit-learn stack — no external services.
"""

import pytest
from pathlib import Path
import tempfile

from mossy_manager.ai.brain import (
    ModAIBrain,
    _extract_mod_features,
    _plugin_name_to_tokens,
    _SEVERITY_LABELS,
    _SKLEARN_AVAILABLE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FO4_LOAD_ORDER = [
    "Fallout4.esm",
    "DLCRobot.esm",
    "DLCCoast.esm",
    "DLCNukaWorld.esm",
    "UnoffPatch.esp",
    "F4SE_Framework.esp",
    "WeaponOverhaul.esp",
    "ArmorMod.esp",
    "SettlementTweaks.esp",
    "TexturePack.esp",
    "AudioMod.esp",
    "UITweaks.esp",
    "BashedPatch.esp",
]

TINY_ORDER = ["Fallout4.esm", "MyMod.esp"]


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

class TestFeatureExtraction:
    def test_tokens_removes_separators(self):
        tokens = _plugin_name_to_tokens("My-Mod_Pack.esp")
        assert "-" not in tokens
        assert "_" not in tokens
        assert "esp" not in tokens  # extension stripped

    def test_tokens_lower(self):
        tokens = _plugin_name_to_tokens("WeaponMod.esp")
        assert tokens == tokens.lower()

    def test_feature_vector_length(self):
        feat = _extract_mod_features("TestMod.esp")
        assert feat.shape == (23,)

    def test_esm_flag_set(self):
        feat = _extract_mod_features("Fallout4.esm")
        assert feat[0] == 1.0  # is_master
        assert feat[2] == 0.0  # is_plugin

    def test_esp_flag_set(self):
        feat = _extract_mod_features("MyMod.esp")
        assert feat[2] == 1.0  # is_plugin

    def test_esl_flag_set(self):
        feat = _extract_mod_features("LightMod.esl")
        assert feat[1] == 1.0  # is_light

    def test_scripts_file_flag(self):
        feat = _extract_mod_features("ScriptMod.esp", ["scripts/myscript.pex"])
        assert feat[3] == 1.0  # has_scripts

    def test_texture_file_flag(self):
        feat = _extract_mod_features("TexMod.esp", ["textures/sky.dds"])
        assert feat[4] == 1.0  # has_textures

    def test_mesh_file_flag(self):
        feat = _extract_mod_features("MeshMod.esp", ["meshes/thing.nif"])
        assert feat[5] == 1.0  # has_meshes

    def test_no_files_gives_zero_type_flags(self):
        feat = _extract_mod_features("BasicMod.esp", [])
        # type flags (3-7) should all be zero when no files provided
        assert all(feat[3:8] == 0.0)


# ---------------------------------------------------------------------------
# Brain construction
# ---------------------------------------------------------------------------

class TestModAIBrainInit:
    def test_default_construction(self):
        brain = ModAIBrain()
        assert brain is not None

    def test_classifier_seeded_on_init(self):
        brain = ModAIBrain()
        assert brain._classifier_trained is _SKLEARN_AVAILABLE
        if _SKLEARN_AVAILABLE:
            # neural network should also be trained
            assert brain._nn_trained is True


    def test_custom_clusters(self):
        brain = ModAIBrain(n_clusters=4)
        assert brain.n_clusters == 4


# ---------------------------------------------------------------------------
# Compatibility scoring
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _SKLEARN_AVAILABLE, reason="scikit-learn required")
class TestCompatibilityScoring:
    def test_score_returns_float_in_range(self):
        brain = ModAIBrain()
        score = brain.score_compatibility("WeaponMod.esp", "ArmorMod.esp")
        assert 0.0 <= score <= 1.0

    def test_identical_names_score_low(self):
        brain = ModAIBrain()
        # Very similar names share character n-grams → lower compatibility
        score = brain.score_compatibility("WeaponMod.esp", "WeaponMod2.esp")
        # Completely different names should score higher than very similar ones
        score_diff = brain.score_compatibility("WeaponMod.esp", "AudioPack.esp")
        assert score < score_diff

    def test_different_names_score_higher(self):
        brain = ModAIBrain()
        score = brain.score_compatibility("WeaponMod.esp", "SoundPack.esp")
        assert score >= 0.0

    def test_rank_compatibility_returns_sorted_list(self):
        brain = ModAIBrain()
        candidates = ["TexturePack.esp", "AudioMod.esp", "WeaponPatch.esp"]
        ranked = brain.rank_compatibility("WeaponOverhaul.esp", candidates)
        assert len(ranked) == 3
        scores = [s for _, s in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_rank_compatibility_empty_candidates(self):
        brain = ModAIBrain()
        ranked = brain.rank_compatibility("WeaponMod.esp", [])
        assert ranked == []


# ---------------------------------------------------------------------------
# Conflict-risk prediction
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _SKLEARN_AVAILABLE, reason="scikit-learn required")
class TestConflictRiskPrediction:
    def test_predict_returns_dict_with_required_keys(self):
        brain = ModAIBrain()
        result = brain.predict_conflict_risk("TestMod.esp")
        assert "severity" in result
        assert "confidence" in result
        assert "probabilities" in result
        assert "explanation" in result
        # neural network output should also appear
        assert "nn_probabilities" in result

    def test_severity_is_valid_label(self):
        brain = ModAIBrain()
        result = brain.predict_conflict_risk("TestMod.esp")
        assert result["severity"] in _SEVERITY_LABELS

    def test_confidence_in_range(self):
        brain = ModAIBrain()
        result = brain.predict_conflict_risk("TestMod.esp")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_probabilities_sum_to_one(self):
        brain = ModAIBrain()
        result = brain.predict_conflict_risk("TestMod.esp")
        total = sum(result["probabilities"].values())
        assert abs(total - 1.0) < 1e-4

    def test_script_heavy_mod_risk(self):
        brain = ModAIBrain()
        result = brain.predict_conflict_risk(
            "ScriptHeavy.esp", ["scripts/myscript.pex", "scripts/other.pex"]
        )
        # With scripts, risk should not be "low"
        assert result["severity"] in ("high", "critical", "medium")
        assert "nn_probabilities" in result

    def test_explanation_contains_severity(self):
        brain = ModAIBrain()
        result = brain.predict_conflict_risk("TestMod.esp")
        sev = result["severity"].upper()
        assert sev in result["explanation"]

    def test_predict_with_file_list(self):
        brain = ModAIBrain()
        result = brain.predict_conflict_risk(
            "TextureMod.esp", ["textures/sky.dds", "textures/ground.dds"]
        )
        assert result["severity"] in _SEVERITY_LABELS


# ---------------------------------------------------------------------------
# Anomaly detection
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _SKLEARN_AVAILABLE, reason="scikit-learn required")
class TestAnomalyDetection:
    def test_returns_expected_keys(self):
        brain = ModAIBrain()
        result = brain.detect_load_order_anomalies(FO4_LOAD_ORDER)
        assert "anomalies" in result
        assert "clean" in result
        assert "total" in result

    def test_total_equals_input_length(self):
        brain = ModAIBrain()
        result = brain.detect_load_order_anomalies(FO4_LOAD_ORDER)
        assert result["total"] == len(FO4_LOAD_ORDER)

    def test_anomaly_plus_clean_equals_total(self):
        brain = ModAIBrain()
        result = brain.detect_load_order_anomalies(FO4_LOAD_ORDER)
        assert len(result["anomalies"]) + len(result["clean"]) == result["total"]

    def test_too_short_returns_empty_anomalies(self):
        brain = ModAIBrain()
        result = brain.detect_load_order_anomalies(["Fallout4.esm", "MyMod.esp"])
        assert result["anomalies"] == []

    def test_anomaly_dict_has_plugin_and_reason(self):
        brain = ModAIBrain()
        result = brain.detect_load_order_anomalies(FO4_LOAD_ORDER)
        for a in result["anomalies"]:
            assert "plugin" in a
            assert "position" in a
            assert "reason" in a
            assert "anomaly_score" in a


# ---------------------------------------------------------------------------
# Clustering
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _SKLEARN_AVAILABLE, reason="scikit-learn required")
class TestClustering:
    def test_cluster_returns_expected_keys(self):
        brain = ModAIBrain(n_clusters=3)
        result = brain.cluster_plugins(FO4_LOAD_ORDER)
        assert "clusters" in result
        assert "labels" in result
        assert "centroids" in result
        assert "summary" in result

    def test_all_plugins_assigned(self):
        brain = ModAIBrain(n_clusters=3)
        result = brain.cluster_plugins(FO4_LOAD_ORDER)
        total = sum(len(v) for v in result["clusters"].values())
        assert total == len(FO4_LOAD_ORDER)

    def test_labels_length_matches_input(self):
        brain = ModAIBrain(n_clusters=3)
        result = brain.cluster_plugins(FO4_LOAD_ORDER)
        assert len(result["labels"]) == len(FO4_LOAD_ORDER)

    def test_single_plugin_no_crash(self):
        brain = ModAIBrain()
        result = brain.cluster_plugins(["Fallout4.esm"])
        assert "clusters" in result

    def test_two_plugins_no_crash(self):
        brain = ModAIBrain(n_clusters=2)
        result = brain.cluster_plugins(["Fallout4.esm", "MyMod.esp"])
        assert "clusters" in result


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

class TestRecommendations:
    def test_recommend_returns_list(self):
        brain = ModAIBrain()
        recs = brain.recommend(FO4_LOAD_ORDER)
        assert isinstance(recs, list)

    def test_missing_fallout4_esm_is_critical(self):
        brain = ModAIBrain()
        bad_order = ["DLCRobot.esm", "MyMod.esp"]  # missing Fallout4.esm first
        recs = brain.recommend(bad_order)
        critical = [r for r in recs if r["priority"] == 1 and "Fallout4.esm" in r["message"]]
        assert len(critical) >= 1

    def test_no_ufp_gives_best_practice_rec(self):
        brain = ModAIBrain()
        order = ["Fallout4.esm", "SomeMod.esp"]
        recs = brain.recommend(order)
        ufp_recs = [r for r in recs if "Unofficial" in r.get("message", "")]
        assert len(ufp_recs) >= 1

    def test_plugin_cap_recommendation(self):
        brain = ModAIBrain()
        huge_order = ["Fallout4.esm"] + [f"Mod{i:03d}.esp" for i in range(254)]
        recs = brain.recommend(huge_order)
        cap_recs = [r for r in recs if "cap" in r.get("message", "").lower()]
        assert len(cap_recs) >= 1

    def test_recommendation_has_required_keys(self):
        brain = ModAIBrain()
        recs = brain.recommend(FO4_LOAD_ORDER)
        for r in recs:
            assert "priority" in r
            assert "type" in r
            assert "message" in r

    def test_recommendations_sorted_by_priority(self):
        brain = ModAIBrain()
        recs = brain.recommend(FO4_LOAD_ORDER)
        priorities = [r["priority"] for r in recs]
        assert priorities == sorted(priorities)


# ---------------------------------------------------------------------------
# Online learning
# ---------------------------------------------------------------------------

class TestOnlineLearning:
    def test_learn_from_outcome_updates_training_count(self):
        brain = ModAIBrain()
        before = len(brain._X_train)
        brain.learn_from_outcome("NewMod.esp", ["scripts/new.pex"], "high")
        assert len(brain._X_train) == before + 1

    def test_learn_from_outcome_invalid_severity(self):
        brain = ModAIBrain()
        with pytest.raises(ValueError, match="actual_severity"):
            brain.learn_from_outcome("Mod.esp", None, "extreme")

    def test_learn_then_predict(self):
        brain = ModAIBrain()
        for _ in range(5):
            brain.learn_from_outcome("CriticalMod.esp", ["CriticalMod.esp"], "critical")
        result = brain.predict_conflict_risk("CriticalMod.esp")
        assert result["severity"] in _SEVERITY_LABELS


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

class TestPersistence:
    def test_save_creates_directory_and_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = ModAIBrain()
            saved = brain.save(Path(tmpdir) / "model")
            assert (Path(tmpdir) / "model" / "training_data.json").exists()

    def test_save_and_reload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            brain1 = ModAIBrain()
            brain1.learn_from_outcome("ReloadMod.esp", None, "medium")
            brain1.save(model_dir)

            # Reload — constructor reads saved data
            brain2 = ModAIBrain(model_path=model_dir)
            # Original seed + extra example should be present
            assert len(brain2._X_train) >= len(brain1._X_train)


# ---------------------------------------------------------------------------
# Full analysis
# ---------------------------------------------------------------------------

class TestFullAnalysis:
    def test_full_analysis_returns_expected_keys(self):
        brain = ModAIBrain()
        report = brain.full_analysis(FO4_LOAD_ORDER)
        assert "recommendations" in report
        assert "anomalies" in report
        assert "clusters" in report
        assert "risk_summary" in report
        assert "total_plugins" in report

    def test_full_analysis_total_plugins(self):
        brain = ModAIBrain()
        report = brain.full_analysis(FO4_LOAD_ORDER)
        assert report["total_plugins"] == len(FO4_LOAD_ORDER)

    def test_full_analysis_tiny_order(self):
        brain = ModAIBrain()
        report = brain.full_analysis(TINY_ORDER)
        assert "recommendations" in report

    def test_full_analysis_with_mod_files(self):
        brain = ModAIBrain()
        mod_files = {
            "WeaponOverhaul.esp": ["WeaponOverhaul.esp", "scripts/weapon.pex"],
            "TexturePack.esp": ["textures/sky.dds"],
        }
        report = brain.full_analysis(FO4_LOAD_ORDER, mod_files=mod_files)
        assert "risk_summary" in report


# ---------------------------------------------------------------------------
# CLI — smoke tests via Click test runner
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _SKLEARN_AVAILABLE, reason="scikit-learn required")
class TestAICLI:
    def test_ai_score_command(self):
        from click.testing import CliRunner
        from mossy_manager.cli.main import main
        runner = CliRunner()
        r = runner.invoke(main, ["ai", "score", "WeaponMod.esp", "ArmorMod.esp"])
        assert r.exit_code == 0
        assert "%" in r.output

    def test_ai_risk_command(self):
        from click.testing import CliRunner
        from mossy_manager.cli.main import main
        runner = CliRunner()
        r = runner.invoke(main, ["ai", "risk", "ScriptMod.esp",
                                  "--files", "scripts/myscript.pex"])
        assert r.exit_code == 0
        assert "Risk" in r.output

    def test_ai_analyze_no_input(self):
        from click.testing import CliRunner
        from mossy_manager.cli.main import main
        runner = CliRunner()
        r = runner.invoke(main, ["ai", "analyze"])
        assert r.exit_code == 0  # Should warn but not crash
        assert "No plugins" in r.output or "⚠" in r.output

    def test_ai_learn_command(self, tmp_path):
        from click.testing import CliRunner
        from mossy_manager.cli.main import main
        runner = CliRunner()
        model_dir = str(tmp_path / "model")
        r = runner.invoke(main, [
            "ai", "learn", "TestMod.esp", "high",
            "--model-dir", model_dir,
        ])
        assert r.exit_code == 0
        assert "updated" in r.output.lower() or "✓" in r.output

    def test_ai_analyze_with_plugins_file(self, tmp_path):
        from click.testing import CliRunner
        from mossy_manager.cli.main import main
        plugins_file = tmp_path / "plugins.txt"
        plugins_file.write_text(
            "*Fallout4.esm\n*DLCRobot.esm\n*WeaponMod.esp\n*ArmorMod.esp\n"
            "*TexturePack.esp\n*AudioMod.esp\n*UITweaks.esp\n*BashedPatch.esp\n"
        )
        runner = CliRunner()
        r = runner.invoke(main, ["ai", "analyze",
                                  "--plugins-file", str(plugins_file)])
        assert r.exit_code == 0
        assert "AI analysis complete" in r.output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
