"""
Mossy Manager AI Brain
======================
Machine-learning powered problem-solving for Fallout 4 mod management.
All capabilities use free, open-source libraries only (scikit-learn + numpy).

Features
--------
1. **Compatibility scoring** — TF-IDF vectorisation of plugin names + cosine
   similarity to score how likely two mods are to conflict.
2. **Category clustering** — K-Means groups unknown plugins into behavioural
   buckets so you can spot over-represented mod types.
3. **Conflict-risk prediction** — A Random-Forest classifier trained on
   hand-crafted feature vectors (file-type counts, name patterns) predicts
   whether a given mod will produce critical, high, medium or low conflicts.
4. **Load-order anomaly detection** — An Isolation Forest flags plugins whose
   position in the load order is statistically unusual given the rest of the
   setup (e.g. a patch loading before its masters).
5. **Smart recommendations** — Combines all four signals plus the existing
   Fallout 4 rule engine to produce a ranked, explained recommendation list.
6. **Online learning** — Every conflict/resolution outcome can be fed back as
   training data so the model improves over time without any external service.
"""

from __future__ import annotations

import json
import logging
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy sklearn imports — graceful degradation when scikit-learn is not installed
# ---------------------------------------------------------------------------

def _require_sklearn(feature: str):
    """Raise an informative error when scikit-learn is missing."""
    raise ImportError(
        f"scikit-learn is required for AI feature '{feature}'. "
        "Install it with:  pip install scikit-learn"
    )


try:
    from sklearn.cluster import KMeans
    from sklearn.ensemble import IsolationForest, RandomForestClassifier
    from sklearn.neural_network import MLPClassifier
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.preprocessing import LabelEncoder
    _SKLEARN_AVAILABLE = True
except ImportError:  # pragma: no cover
    _SKLEARN_AVAILABLE = False


# ---------------------------------------------------------------------------
# Feature extraction helpers
# ---------------------------------------------------------------------------

# Fallout 4 specific token vocabulary used for all text features
_FO4_TOKEN_HINTS = [
    "unofficial", "patch", "fix", "f4se", "mcm", "framework", "library",
    "overhaul", "rebalance", "settlement", "workshop", "weapon", "armor",
    "texture", "visual", "enb", "lighting", "weather", "audio", "sound",
    "npc", "companion", "quest", "world", "ui", "hud", "interface",
    "script", "pex", "esp", "esm", "esl", "dds", "nif", "wav",
    "bodyslide", "cbbe", "sim", "arbitration", "loot", "bashed",
    "merged", "compat", "conflict", "resolution",
]

# Severity labels used by the classifier
_SEVERITY_LABELS = ["low", "medium", "high", "critical"]


def _plugin_name_to_tokens(name: str) -> str:
    """Convert a plugin filename to a space-separated token string."""
    stem = Path(name).stem.lower()
    # Replace separators with spaces so TF-IDF splits tokens naturally
    for ch in "-_.,()[]":
        stem = stem.replace(ch, " ")
    return stem


def _extract_mod_features(
    mod_name: str,
    file_list: Optional[List[str]] = None,
) -> np.ndarray:
    """
    Build a fixed-length numeric feature vector for a single mod.

    Dimensions (23 total):
     0   : is_master (.esm)
     1   : is_light  (.esl)
     2   : is_plugin (.esp)
     3   : has_scripts (.pex/.psc)
     4   : has_textures (.dds/.tga)
     5   : has_meshes (.nif/.tri/.hkx)
     6   : has_audio  (.wav/.fuz/.xwm/.mp3)
     7   : has_config (.ini/.json/.xml/.cfg/.txt)
     8-22: name token hits for each entry in _FO4_TOKEN_HINTS[:15]
    """
    name_lower = mod_name.lower()
    stem = Path(mod_name).stem.lower()

    feat = np.zeros(23, dtype=float)

    # Plugin type
    feat[0] = float(name_lower.endswith(".esm"))
    feat[1] = float(name_lower.endswith(".esl"))
    feat[2] = float(name_lower.endswith(".esp"))

    # File-type presence (from file list if provided)
    if file_list:
        files_lower = [f.lower() for f in file_list]
        feat[3] = float(any(f.endswith((".pex", ".psc")) for f in files_lower))
        feat[4] = float(any(f.endswith((".dds", ".tga")) for f in files_lower))
        feat[5] = float(any(f.endswith((".nif", ".tri", ".hkx")) for f in files_lower))
        feat[6] = float(any(f.endswith((".wav", ".fuz", ".xwm", ".mp3")) for f in files_lower))
        feat[7] = float(any(f.endswith((".ini", ".json", ".xml", ".cfg", ".txt")) for f in files_lower))

    # Name token hits (first 15 hints only to stay at dim 23)
    for i, token in enumerate(_FO4_TOKEN_HINTS[:15]):
        feat[8 + i] = float(token in stem)

    return feat


# ---------------------------------------------------------------------------
# Training data seed
# ---------------------------------------------------------------------------

# Hand-crafted seed examples so the classifier is useful out of the box
# without any real game data.  Format: (mod_name, file_list, severity_label)
_SEED_TRAINING_DATA: List[Tuple[str, List[str], str]] = [
    # critical — direct plugin conflicts
    ("ConflictMod_A.esp",       ["ConflictMod_A.esp"],               "critical"),
    ("ConflictMod_B.esp",       ["ConflictMod_B.esp"],               "critical"),
    ("WeaponOverride.esp",      ["WeaponOverride.esp"],              "critical"),
    ("NPCOverride.esp",         ["NPCOverride.esp"],                 "critical"),
    # high — script conflicts
    ("ScriptHeavy.esp",         ["scripts/ScriptHeavy.pex"],         "high"),
    ("F4SE_Plugin.esp",         ["scripts/f4se_plugin.pex"],         "high"),
    ("MCM_Settings.esp",        ["scripts/mcm_settings.pex"],        "high"),
    ("QuestOverhaul.esp",       ["scripts/quest.pex", "quest.esp"],  "high"),
    # medium — texture / mesh conflicts
    ("TexturePack.esp",         ["textures/sky.dds"],                "medium"),
    ("ArmorRetexture.esp",      ["textures/armor.dds"],              "medium"),
    ("WeaponMeshes.esp",        ["meshes/weapon.nif"],               "medium"),
    ("BodyReplacer.esp",        ["meshes/body.nif", "body.dds"],     "medium"),
    # low — config / audio only
    ("RadioStation.esp",        ["audio/radio.wav"],                 "low"),
    ("UITweaks.esp",            ["interface/ui.swf"],                "low"),
    ("INITweaks.ini",           ["fallout4.ini"],                    "low"),
    ("AudioPack.esp",           ["audio/ambience.fuz"],              "low"),
    # more variety
    ("UnoffPatch.esp",          ["UnoffPatch.esp"],                  "critical"),
    ("SettlementOverhaul.esp",  ["scripts/settlement.pex",
                                 "meshes/settlement.nif"],           "high"),
    ("ENBPreset.esp",           ["enbseries.ini"],                   "low"),
    ("WeatherMod.esp",          ["textures/weather.dds"],            "medium"),
]


# ---------------------------------------------------------------------------
# Main AI class
# ---------------------------------------------------------------------------

class ModAIBrain:
    """
    AI-powered assistant for Fallout 4 mod management.

    Parameters
    ----------
    model_path : Path or None
        Optional directory where trained model state is persisted.
        If *None* the brain operates purely in-memory.
    n_clusters : int
        Number of K-Means clusters for the category clustering feature.
    random_state : int
        Seed for reproducible results in all stochastic estimators.
    """

    def __init__(
        self,
        model_path: Optional[Path] = None,
        n_clusters: int = 8,
        random_state: int = 42,
    ) -> None:
        self.model_path = model_path
        self.n_clusters = n_clusters
        self.random_state = random_state

        # ── text similarity ──────────────────────────────────────────────
        if _SKLEARN_AVAILABLE:
            self._tfidf = TfidfVectorizer(
                analyzer="char_wb",
                ngram_range=(2, 4),
                min_df=1,
                sublinear_tf=True,
            )
        else:
            self._tfidf = None

        # ── clustering ───────────────────────────────────────────────────
        self._kmeans: Optional[Any] = None
        self._cluster_labels: List[str] = []

        # ── classifier ───────────────────────────────────────────────────
        if _SKLEARN_AVAILABLE:
            self._classifier = RandomForestClassifier(
                n_estimators=100,
                max_depth=6,
                random_state=random_state,
            )
            # a simple multilayer perceptron for 'neural' recommendations
            self._nn_classifier = MLPClassifier(
                hidden_layer_sizes=(32,16),
                max_iter=300,
                random_state=random_state,
            )
        else:
            self._classifier = None
            self._nn_classifier = None
        self._classifier_trained = False
        self._nn_trained = False
        self._label_encoder = LabelEncoder() if _SKLEARN_AVAILABLE else None

        # ── anomaly detector ─────────────────────────────────────────────
        if _SKLEARN_AVAILABLE:
            self._anomaly_detector = IsolationForest(
                contamination=0.1,
                random_state=random_state,
            )
        else:
            self._anomaly_detector = None
        self._anomaly_trained = False

        # ── online training buffer ───────────────────────────────────────
        self._X_train: List[np.ndarray] = []
        self._y_train: List[str] = []

        # Seed the classifier from hard-coded examples so it works out of the box
        self._seed_classifier()

        # Load persisted state if available
        if model_path and (Path(model_path) / "training_data.json").exists():
            self._load_training_data(model_path)

    # ------------------------------------------------------------------ #
    #  1. Compatibility scoring                                           #
    # ------------------------------------------------------------------ #

    def score_compatibility(self, plugin_a: str, plugin_b: str) -> float:
        """
        Score the compatibility between two plugins (0 = likely conflict, 1 = safe).

        Uses TF-IDF cosine similarity on plugin name tokens.  Low similarity
        means the plugins touch different areas (good); high similarity means
        they probably override the same records (risky).

        Returns
        -------
        float
            A value in [0, 1] where **1.0 = highly compatible** and
            **0.0 = likely to conflict**.
        """
        if not _SKLEARN_AVAILABLE:
            _require_sklearn("score_compatibility")

        tokens_a = _plugin_name_to_tokens(plugin_a)
        tokens_b = _plugin_name_to_tokens(plugin_b)

        corpus = [tokens_a, tokens_b]
        try:
            mat = self._tfidf.fit_transform(corpus)
            sim = float(cosine_similarity(mat[0:1], mat[1:2])[0][0])
        except Exception:
            sim = 0.0

        # Invert: high textual similarity → lower compatibility score
        return round(1.0 - sim, 4)

    def rank_compatibility(
        self, target: str, candidates: List[str]
    ) -> List[Tuple[str, float]]:
        """
        Rank a list of candidate plugins by compatibility with *target*.

        Returns a list of ``(plugin_name, score)`` sorted best-first.
        """
        if not _SKLEARN_AVAILABLE:
            _require_sklearn("rank_compatibility")

        scored = [(c, self.score_compatibility(target, c)) for c in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    # ------------------------------------------------------------------ #
    #  2. Category clustering                                             #
    # ------------------------------------------------------------------ #

    def cluster_plugins(
        self, plugins: List[str]
    ) -> Dict[str, Any]:
        """
        Group plugins into *n_clusters* behavioural clusters using K-Means.

        Returns
        -------
        dict with keys:
          ``clusters``   — mapping cluster_id → list of plugin names
          ``labels``     — list of cluster ids parallel to *plugins*
          ``centroids``  — centroid feature vector per cluster (as lists)
          ``summary``    — human-readable description per cluster
        """
        if not _SKLEARN_AVAILABLE:
            _require_sklearn("cluster_plugins")

        if len(plugins) < 2:
            # Nothing meaningful to cluster
            return {
                "clusters": {0: plugins},
                "labels": [0] * len(plugins),
                "centroids": [],
                "summary": {0: "Only one plugin — no clustering possible."},
            }

        k = min(self.n_clusters, len(plugins))
        X = np.vstack([_extract_mod_features(p) for p in plugins])

        km = KMeans(n_clusters=k, random_state=self.random_state, n_init="auto")
        km.fit(X)
        self._kmeans = km

        clusters: Dict[int, List[str]] = {}
        for plugin, label in zip(plugins, km.labels_):
            clusters.setdefault(int(label), []).append(plugin)

        summary = {}
        for cid, members in clusters.items():
            # Describe the cluster by the most common name tokens
            token_counts: Dict[str, int] = {}
            for m in members:
                for tok in _plugin_name_to_tokens(m).split():
                    if len(tok) > 2:
                        token_counts[tok] = token_counts.get(tok, 0) + 1
            top = sorted(token_counts, key=lambda t: -token_counts[t])[:3]
            tag = ", ".join(top) if top else "mixed"
            summary[cid] = f"Cluster {cid}: {len(members)} plugins — themes: {tag}"

        return {
            "clusters": clusters,
            "labels": [int(l) for l in km.labels_],
            "centroids": km.cluster_centers_.tolist(),
            "summary": summary,
        }

    # ------------------------------------------------------------------ #
    #  3. Conflict-risk prediction                                        #
    # ------------------------------------------------------------------ #

    def _seed_classifier(self) -> None:
        """Train the classifier on the built-in seed data."""
        for mod_name, files, severity in _SEED_TRAINING_DATA:
            self._X_train.append(_extract_mod_features(mod_name, files))
            self._y_train.append(severity)
        self._fit_classifier()

    def _fit_classifier(self) -> None:
        """(Re-)fit the classifiers on all accumulated training data."""
        if not _SKLEARN_AVAILABLE or len(self._X_train) < 4:
            return
        X = np.vstack(self._X_train)
        y = self._label_encoder.fit_transform(self._y_train)
        self._classifier.fit(X, y)
        self._classifier_trained = True
        if self._nn_classifier is not None:
            self._nn_classifier.fit(X, y)
            self._nn_trained = True

    def predict_conflict_risk(
        self,
        mod_name: str,
        file_list: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Predict the conflict-risk severity for a mod.

        Parameters
        ----------
        mod_name : str
            Plugin filename (e.g. ``"MyMod.esp"``).
        file_list : list of str, optional
            Files contained in the mod (relative paths).

        Returns
        -------
        dict with keys:
          ``severity``     — predicted label (low/medium/high/critical)
          ``confidence``   — probability of the top label (0–1)
          ``probabilities``— dict label → probability
          ``explanation``  — human-readable reasoning
        """
        if not _SKLEARN_AVAILABLE:
            _require_sklearn("predict_conflict_risk")

        if not self._classifier_trained:
            return {
                "severity": "unknown",
                "confidence": 0.0,
                "probabilities": {},
                "explanation": "Classifier not yet trained — call learn_from_outcome() with some examples.",
            }

        feat = _extract_mod_features(mod_name, file_list).reshape(1, -1)
        proba = self._classifier.predict_proba(feat)[0]
        classes = self._label_encoder.classes_

        prob_dict = {str(cls): round(float(p), 4) for cls, p in zip(classes, proba)}
        top_idx = int(np.argmax(proba))
        top_label = str(classes[top_idx])
        confidence = round(float(proba[top_idx]), 4)

        explanation = self._build_risk_explanation(mod_name, file_list, top_label, confidence)

        result = {
            "severity": top_label,
            "confidence": confidence,
            "probabilities": prob_dict,
            "explanation": explanation,
        }
        # add neural network probabilities if available
        if self._nn_classifier is not None and self._nn_trained:
            nn_proba = self._nn_classifier.predict_proba(feat)[0]
            result["nn_probabilities"] = {str(cls): round(float(p), 4) for cls, p in zip(classes, nn_proba)}
        return result

    def _build_risk_explanation(
        self,
        mod_name: str,
        file_list: Optional[List[str]],
        severity: str,
        confidence: float,
    ) -> str:
        """Generate a plain-English explanation of the risk prediction."""
        reasons = []
        name_lower = mod_name.lower()

        if name_lower.endswith(".esm"):
            reasons.append("it is a master file (.esm) that other plugins may depend on")
        elif name_lower.endswith(".esl"):
            reasons.append("it is a light plugin (.esl) — lower slot pressure")
        elif name_lower.endswith(".esp"):
            reasons.append("it is a standard plugin (.esp)")

        if file_list:
            has_scripts = any(f.lower().endswith((".pex", ".psc")) for f in file_list)
            has_tex = any(f.lower().endswith((".dds", ".tga")) for f in file_list)
            has_mesh = any(f.lower().endswith((".nif", ".hkx")) for f in file_list)
            if has_scripts:
                reasons.append("it contains compiled scripts (.pex) which are hard to merge")
            if has_tex and has_mesh:
                reasons.append("it replaces both textures and meshes")
            elif has_tex:
                reasons.append("it contains texture replacers (.dds)")
            elif has_mesh:
                reasons.append("it contains mesh replacers (.nif)")

        reason_str = ("; ".join(reasons) + ".") if reasons else "based on name/file patterns."
        pct = int(confidence * 100)
        return (
            f"Predicted severity: {severity.upper()} ({pct}% confidence) — {reason_str}"
        )

    # ------------------------------------------------------------------ #
    #  4. Load-order anomaly detection                                    #
    # ------------------------------------------------------------------ #

    def detect_load_order_anomalies(
        self, load_order: List[str]
    ) -> Dict[str, Any]:
        """
        Detect statistically unusual positions in the load order.

        Each plugin is represented as a feature vector that encodes its
        position (normalised), type, and name-token profile.  The Isolation
        Forest flags outliers — plugins that are out of place.

        Returns
        -------
        dict with keys:
          ``anomalies`` — list of dicts {plugin, position, reason, score}
          ``clean``     — list of plugin names that look fine
          ``total``     — total number of plugins evaluated
        """
        if not _SKLEARN_AVAILABLE:
            _require_sklearn("detect_load_order_anomalies")

        if len(load_order) < 4:
            return {
                "anomalies": [],
                "clean": list(load_order),
                "total": len(load_order),
            }

        n = len(load_order)
        X = []
        for i, plugin in enumerate(load_order):
            feat = _extract_mod_features(plugin)
            pos_norm = i / (n - 1)  # normalised position 0→1
            row = np.concatenate([[pos_norm], feat])
            X.append(row)

        X_arr = np.vstack(X)
        det = IsolationForest(contamination=0.1, random_state=self.random_state)
        preds = det.fit_predict(X_arr)     # -1 = anomaly, 1 = normal
        scores = det.score_samples(X_arr)  # more negative = more anomalous

        anomalies = []
        clean = []
        for i, (plugin, pred, score) in enumerate(zip(load_order, preds, scores)):
            if pred == -1:
                reason = self._explain_position_anomaly(plugin, i, n)
                anomalies.append({
                    "plugin": plugin,
                    "position": i,
                    "anomaly_score": round(float(score), 4),
                    "reason": reason,
                })
            else:
                clean.append(plugin)

        anomalies.sort(key=lambda x: x["anomaly_score"])  # most anomalous first
        return {"anomalies": anomalies, "clean": clean, "total": n}

    def _explain_position_anomaly(self, plugin: str, pos: int, total: int) -> str:
        """Produce a human-readable reason for a flagged plugin."""
        name_lower = plugin.lower()
        pct = int(100 * pos / max(total - 1, 1))

        if name_lower.endswith(".esm") and pct > 20:
            return f"Master file (.esm) at position {pos}/{total} — should be near the top"
        if "patch" in name_lower and pct < 50:
            return f"Patch plugin at position {pos}/{total} — patches typically load late"
        if "unofficial" in name_lower and pct > 30:
            return f"Unofficial Patch at {pct}% into load order — should load early"
        if any(t in name_lower for t in ("bashed", "merged", "smashed")) and pct < 90:
            return f"Merge/bashed patch at {pct}% — should be at the very end"
        return f"Statistically unusual position ({pos}/{total}) for this plugin type"

    # ------------------------------------------------------------------ #
    #  5. Smart recommendations                                           #
    # ------------------------------------------------------------------ #

    def recommend(
        self,
        load_order: List[str],
        mod_files: Optional[Dict[str, List[str]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate a prioritised, AI-explained recommendation list.

        Combines:
        - Conflict-risk predictions for each plugin
        - Load-order anomaly detection
        - Category clustering (over-represented groups)
        - Fallout 4 rule engine (via embedded knowledge)

        Parameters
        ----------
        load_order : list of str
            Ordered list of active plugin names.
        mod_files : dict, optional
            Mapping mod_name → list of relative file paths for richer analysis.

        Returns
        -------
        list of dicts, sorted by priority (highest first):
          ``priority``   — int (1 = critical, 2 = high, 3 = medium, 4 = info)
          ``type``       — str category of recommendation
          ``message``    — human-readable advice
          ``plugin``     — plugin name (if applicable)
          ``ai_detail``  — optional extended explanation from the AI
        """
        recommendations: List[Dict[str, Any]] = []

        # ── A. Load-order anomalies ──────────────────────────────────────
        if _SKLEARN_AVAILABLE and len(load_order) >= 4:
            anomaly_result = self.detect_load_order_anomalies(load_order)
            for anom in anomaly_result["anomalies"]:
                recommendations.append({
                    "priority": 2,
                    "type": "load_order_anomaly",
                    "message": f"Plugin position is unusual: {anom['plugin']}",
                    "plugin": anom["plugin"],
                    "ai_detail": anom["reason"],
                })

        # ── B. Conflict-risk per plugin ──────────────────────────────────
        if _SKLEARN_AVAILABLE and self._classifier_trained:
            for plugin in load_order:
                files = (mod_files or {}).get(plugin)
                risk = self.predict_conflict_risk(plugin, files)
                if risk["severity"] in ("critical", "high") and risk["confidence"] >= 0.5:
                    recommendations.append({
                        "priority": 1 if risk["severity"] == "critical" else 2,
                        "type": "conflict_risk",
                        "message": f"High conflict risk: {plugin}",
                        "plugin": plugin,
                        "ai_detail": risk["explanation"],
                    })

        # ── C. Clustering — over-represented categories ──────────────────
        if _SKLEARN_AVAILABLE and len(load_order) >= 4:
            cluster_result = self.cluster_plugins(load_order)
            for cid, members in cluster_result["clusters"].items():
                if len(members) >= 4:
                    desc = cluster_result["summary"].get(cid, f"Cluster {cid}")
                    recommendations.append({
                        "priority": 3,
                        "type": "category_overload",
                        "message": f"Many similar mods in same category ({len(members)} plugins): {desc}",
                        "plugin": None,
                        "ai_detail": f"Plugins: {', '.join(members[:5])}" + (
                            f" ... and {len(members) - 5} more" if len(members) > 5 else ""
                        ),
                    })

        # ── D. Hard Fallout 4 rule checks (fast, no sklearn needed) ─────
        fo4_recs = self._fo4_rule_recommendations(load_order)
        recommendations.extend(fo4_recs)

        # Sort: priority asc, then alpha by plugin name
        recommendations.sort(key=lambda r: (r["priority"], r.get("plugin") or ""))
        return recommendations

    def _fo4_rule_recommendations(
        self, load_order: List[str]
    ) -> List[Dict[str, Any]]:
        """Embedded Fallout 4 rule knowledge — no sklearn required."""
        recs: List[Dict[str, Any]] = []
        lo_lower = [p.lower() for p in load_order]

        # Missing master file at slot 0
        if load_order and load_order[0] != "Fallout4.esm":
            recs.append({
                "priority": 1,
                "type": "rule_violation",
                "message": "Fallout4.esm must be the first plugin",
                "plugin": "Fallout4.esm",
                "ai_detail": "This is a hard requirement from the engine.",
            })

        # Missing unofficial patch
        has_ufp = any("unofficial" in p and "patch" in p for p in lo_lower)
        if not has_ufp:
            recs.append({
                "priority": 3,
                "type": "best_practice",
                "message": "Consider installing the Unofficial Fallout 4 Patch (UFO4P)",
                "plugin": None,
                "ai_detail": "UFO4P fixes thousands of engine and content bugs.",
            })

        # F4SE mentioned but script extender note
        has_f4se = any("f4se" in p or "mcm" in p for p in lo_lower)
        if has_f4se:
            recs.append({
                "priority": 4,
                "type": "info",
                "message": "F4SE-dependent mods detected — ensure F4SE is installed and up to date",
                "plugin": None,
                "ai_detail": "F4SE must match your exact Fallout 4 version.",
            })

        # Plugin cap
        slot_count = sum(1 for p in load_order if not p.lower().endswith(".esl"))
        if slot_count >= 254:
            recs.append({
                "priority": 1,
                "type": "plugin_cap",
                "message": f"Plugin cap reached ({slot_count}/255) — game will not load",
                "plugin": None,
                "ai_detail": "ESL-flag small ESPs or merge patches immediately.",
            })
        elif slot_count >= 240:
            recs.append({
                "priority": 2,
                "type": "plugin_cap",
                "message": f"Approaching plugin cap ({slot_count}/255)",
                "plugin": None,
                "ai_detail": "Consider ESL-flagging small ESPs to free plugin slots.",
            })

        return recs

    # ------------------------------------------------------------------ #
    #  6. Online learning                                                 #
    # ------------------------------------------------------------------ #

    def learn_from_outcome(
        self,
        mod_name: str,
        file_list: Optional[List[str]],
        actual_severity: str,
    ) -> None:
        """
        Feed a real conflict outcome back into the model.

        Parameters
        ----------
        mod_name : str
            Plugin name.
        file_list : list of str or None
            Files in the mod.
        actual_severity : str
            One of ``"low"``, ``"medium"``, ``"high"``, ``"critical"``.
        """
        if actual_severity not in _SEVERITY_LABELS:
            raise ValueError(
                f"actual_severity must be one of {_SEVERITY_LABELS}, got {actual_severity!r}"
            )
        feat = _extract_mod_features(mod_name, file_list)
        self._X_train.append(feat)
        self._y_train.append(actual_severity)
        self._fit_classifier()
        logger.info(f"AI brain learned from '{mod_name}' → severity={actual_severity} "
                    f"(total training examples: {len(self._X_train)})")

    # ------------------------------------------------------------------ #
    #  7. Persistence                                                     #
    # ------------------------------------------------------------------ #

    def save(self, model_path: Optional[Path] = None) -> Path:
        """
        Persist the training data to disk as JSON.

        Only the raw training examples are saved (not the fitted estimator)
        so that the model directory remains human-readable and small.

        Returns the path where data was saved.
        """
        target = Path(model_path or self.model_path or "./mossy_ai_model")
        target.mkdir(parents=True, exist_ok=True)

        data = {
            "training_examples": [
                {"mod_name": mod_name, "file_list": files, "severity": sev}
                for (mod_name, files, sev) in zip(
                    [f"example_{i}" for i in range(len(self._X_train))],
                    [None] * len(self._X_train),
                    self._y_train,
                )
            ]
        }
        out_path = target / "training_data.json"
        out_path.write_text(json.dumps(data, indent=2))
        logger.info(f"AI model data saved to {out_path}")
        return target

    def _load_training_data(self, model_path: Path) -> None:
        """Reload persisted training examples and re-fit."""
        try:
            raw = json.loads((Path(model_path) / "training_data.json").read_text())
            for ex in raw.get("training_examples", []):
                sev = ex.get("severity", "low")
                if sev in _SEVERITY_LABELS:
                    self._X_train.append(
                        _extract_mod_features(ex.get("mod_name", "unknown.esp"))
                    )
                    self._y_train.append(sev)
            self._fit_classifier()
            logger.info(f"Loaded {len(raw.get('training_examples', []))} training examples from {model_path}")
        except Exception as exc:
            logger.warning(f"Could not load AI training data: {exc}")

    # ------------------------------------------------------------------ #
    #  8. Summary report                                                  #
    # ------------------------------------------------------------------ #

    def full_analysis(
        self,
        load_order: List[str],
        mod_files: Optional[Dict[str, List[str]]] = None,
    ) -> Dict[str, Any]:
        """
        Run all AI analyses and return a single comprehensive report.

        Returns
        -------
        dict with keys:
          ``recommendations`` — prioritised list from :meth:`recommend`
          ``anomalies``       — load-order anomalies
          ``clusters``        — plugin clustering summary
          ``risk_summary``    — count of plugins per risk level
          ``sklearn_available`` — bool flag for transparency
        """
        report: Dict[str, Any] = {
            "sklearn_available": _SKLEARN_AVAILABLE,
            "total_plugins": len(load_order),
        }

        # Recommendations
        report["recommendations"] = self.recommend(load_order, mod_files)

        # Anomalies
        if _SKLEARN_AVAILABLE and len(load_order) >= 4:
            report["anomalies"] = self.detect_load_order_anomalies(load_order)
        else:
            report["anomalies"] = {"anomalies": [], "clean": list(load_order), "total": len(load_order)}

        # Clusters
        if _SKLEARN_AVAILABLE and len(load_order) >= 2:
            report["clusters"] = self.cluster_plugins(load_order)
        else:
            report["clusters"] = {}

        # Risk summary
        risk_summary: Dict[str, int] = {s: 0 for s in _SEVERITY_LABELS}
        if _SKLEARN_AVAILABLE and self._classifier_trained:
            for plugin in load_order:
                files = (mod_files or {}).get(plugin)
                risk = self.predict_conflict_risk(plugin, files)
                risk_summary[risk["severity"]] = risk_summary.get(risk["severity"], 0) + 1
        report["risk_summary"] = risk_summary

        return report
