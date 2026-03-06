from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
import asyncio
import queue as stdlib_queue
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from mossy_manager.ai.brain import ModAIBrain
from mossy_manager.ai.fix_generator import FixGenerator
from mossy_manager.ai.reasoner import ModReasoner
from mossy_manager.config_manager import ConfigManager
from mossy_manager.core.conflict_resolver import ConflictResolver
from mossy_manager.games.fallout4 import Fallout4Rules
from mossy_manager.integrations.mo2 import MO2Integration
from mossy_manager.utils.health_checker import ModHealthChecker
from mossy_manager.utils.xedit_integration import XEditIntegration


class OptimizeRequest(BaseModel):
    mo2_path: Optional[str] = None
    profile: str
    apply: bool = False
    backup: bool = True
    # additional options that mirror CLI
    scan_conflicts: bool = False
    resolve_xedit: bool = False
    xedit_path: Optional[str] = None
    patch_name: str = "MossyManager_ConflictPatch"


class ConflictScanRequest(BaseModel):
    mo2_path: Optional[str] = None
    profile: Optional[str] = None


class ConflictScanResponse(BaseModel):
    scanned_mods: int
    stats: dict


class LoadOrderResponse(BaseModel):
    profile: str
    load_order: List[str]
    enabled: dict


class VersionResponse(BaseModel):
    current: str
    latest: Optional[str] = None
    update_available: bool = False


class ModsListResponse(BaseModel):
    mods: List[str]


class MergeRequest(BaseModel):
    mo2_path: Optional[str] = None
    mods: List[str]


class WebhookRequest(BaseModel):
    mo2_path: Optional[str] = None
    profile: str


static_dir = Path(__file__).parent / "static"

# thread-safe progress broadcaster — works from sync and async contexts
_stream_clients: List[stdlib_queue.Queue] = []

def send_progress(message: str):
    for q in list(_stream_clients):
        try:
            q.put_nowait(message)
        except stdlib_queue.Full:
            pass


def _ensure_mo2(mo2_path: Optional[str]) -> MO2Integration:
    if mo2_path:
        mo2 = MO2Integration(Path(mo2_path))
        return mo2
    detected = MO2Integration.detect_mo2_installation()
    if not detected:
        raise HTTPException(status_code=404, detail="Mod Organizer 2 not found. Specify mo2_path.")
    return MO2Integration(detected)


def _detect_xedit_path(mo2: Optional[MO2Integration]) -> Optional[Path]:
    # Reuse config if present
    cfg = ConfigManager()
    cfg_path = cfg.get_config("xedit_path")
    if cfg_path:
        candidate = Path(cfg_path)
        if candidate.exists():
            return candidate

    if mo2:
        tool = mo2.find_tool(["FO4Edit.exe", "xEdit.exe", "SSEEdit.exe", "TES5Edit.exe"])
        if tool:
            return tool

    # Fallback: try detect with default search roots
    search_roots = []
    if mo2 and mo2.mo2_path:
        search_roots.append(mo2.mo2_path)
        tools_dir = Path(mo2.mo2_path) / "tools"
        if tools_dir.exists():
            search_roots.append(tools_dir)

    xe = XEditIntegration()
    detected = xe.detect_xedit("fallout4", search_roots=search_roots) if search_roots else xe.detect_xedit("fallout4")
    return detected


def build_app() -> FastAPI:
    app = FastAPI(title="Mossy Manager UI", version="0.1.0")

    # Serve static frontend
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    @app.get("/api/mo2")
    def get_mo2_info(mo2_path: Optional[str] = None):
        mo2 = _ensure_mo2(mo2_path)
        profiles = mo2.list_profiles() or []
        return {
            "mo2_path": str(mo2.mo2_path) if mo2.mo2_path else None,
            "profiles": profiles,
        }

    @app.get("/api/loadorder", response_model=LoadOrderResponse)
    def get_load_order(profile: str, mo2_path: Optional[str] = None):
        mo2 = _ensure_mo2(mo2_path)
        if profile not in mo2.list_profiles():
            raise HTTPException(status_code=404, detail=f"Profile '{profile}' not found")
        load_order = mo2.read_loadorder_txt(profile)
        enabled = mo2.read_plugins_txt(profile)
        if not load_order:
            raise HTTPException(status_code=404, detail="No plugins found in profile")
        return LoadOrderResponse(profile=profile, load_order=load_order, enabled=enabled)

    @app.post("/api/loadorder/optimize")
    def optimize_load_order(payload: OptimizeRequest):
        # progress events
        send_progress(f"Optimizing profile {payload.profile}")
        mo2 = _ensure_mo2(payload.mo2_path)
        profiles = mo2.list_profiles()
        if payload.profile not in profiles:
            raise HTTPException(status_code=404, detail=f"Profile '{payload.profile}' not found")

        current_order = mo2.read_loadorder_txt(payload.profile)
        plugins_enabled = mo2.read_plugins_txt(payload.profile)
        if not current_order:
            raise HTTPException(status_code=404, detail="No plugins found in profile")

        issues = Fallout4Rules.validate_load_order(current_order)
        send_progress("Load order validated")
        optimized = Fallout4Rules.optimize_load_order(current_order)
        send_progress("Load order optimized")

        moved = []
        index_map = {name: i for i, name in enumerate(current_order)}
        for new_idx, name in enumerate(optimized):
            old_idx = index_map.get(name)
            if old_idx is not None and old_idx != new_idx:
                moved.append({"plugin": name, "from": old_idx, "to": new_idx})

        recommendations = Fallout4Rules.get_recommendations(optimized)

        backup_path = None
        applied = False
        if payload.apply:
            if payload.backup:
                profile_path = mo2.get_profile_path(payload.profile)
                if profile_path:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_dir = profile_path.parent / f"{payload.profile}_backup_{timestamp}"
                    import shutil

                    shutil.copytree(profile_path, backup_dir)
                    backup_path = str(backup_dir)

            optimized_plugins = {p: plugins_enabled.get(p, True) for p in optimized}
            mo2.write_plugins_txt(payload.profile, optimized_plugins)
            mo2.write_loadorder_txt(payload.profile, optimized)
            applied = True

        # conflict handling options
        conflict_report = None
        xedit_result = None
        if payload.scan_conflicts or payload.resolve_xedit:
            resolver = ConflictResolver(Path(mo2.mods_path or '.'))
            for mod_dir in Path(mo2.mods_path or '.').iterdir():
                if mod_dir.is_dir():
                    resolver.scan_mod_files(mod_dir.name, mod_dir)
            conflict_report = resolver.generate_report()
            stats = resolver.get_statistics()
            if payload.resolve_xedit:
                xe = XEditIntegration(xedit_path=Path(payload.xedit_path) if payload.xedit_path else None)
                xedit_result = xe.create_conflict_resolution_patch(
                    conflicts=resolver.export_for_xedit(),
                    patch_name=payload.patch_name,
                    output_dir=Path('.') / 'xedit_output'
                )
        
        return {
            "profile": payload.profile,
            "applied": applied,
            "backup": backup_path,
            "issues": issues,
            "recommendations": recommendations,
            "current_order": current_order,
            "optimized_order": optimized,
            "moved": moved,
            "conflict_report": conflict_report,
            "conflict_stats": stats if payload.scan_conflicts else None,
            "xedit_result": xedit_result,
        }

    @app.post("/api/conflicts/scan", response_model=ConflictScanResponse)
    def scan_conflicts(payload: ConflictScanRequest):
        send_progress("Starting conflict scan")
        mo2 = _ensure_mo2(payload.mo2_path)
        mods_path = mo2.mods_path
        if not mods_path or not mods_path.exists():
            raise HTTPException(status_code=404, detail="Mods directory not found")

        resolver = ConflictResolver(mods_path)
        scanned = 0
        for mod_dir in mods_path.iterdir():
            if mod_dir.is_dir():
                send_progress(f"Scanning {mod_dir.name}")
                resolver.scan_mod_files(mod_dir.name, mod_dir)
                scanned += 1

        stats = resolver.get_statistics()
        send_progress("Conflict scan complete")
        return ConflictScanResponse(scanned_mods=scanned, stats=stats)

    @app.get("/api/stream")
    async def stream_progress(request: Request):
        q: stdlib_queue.Queue = stdlib_queue.Queue(maxsize=100)
        _stream_clients.append(q)

        async def event_generator():
            try:
                while True:
                    if await request.is_disconnected():
                        break
                    try:
                        msg = q.get_nowait()
                        yield f"data: {msg}\n\n"
                    except stdlib_queue.Empty:
                        await asyncio.sleep(0.05)
            finally:
                if q in _stream_clients:
                    _stream_clients.remove(q)

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @app.get("/api/tools")
    def tool_status(mo2_path: Optional[str] = None):
        mo2 = None
        try:
            mo2 = _ensure_mo2(mo2_path)
        except HTTPException:
            mo2 = None
        xedit_path = _detect_xedit_path(mo2)
        return {
            "mo2_path": str(mo2.mo2_path) if mo2 and mo2.mo2_path else None,
            "mods_path": str(mo2.mods_path) if mo2 and mo2.mods_path else None,
            "xedit_path": str(xedit_path) if xedit_path else None,
        }

    # version info (fully offline — no network requests)
    @app.get("/api/version", response_model=VersionResponse)
    def get_version():
        import mossy_manager
        current = mossy_manager.__version__
        return VersionResponse(current=current, latest=current, update_available=False)

    # mod listing and merge endpoints
    @app.get("/api/mods", response_model=ModsListResponse)
    def list_mods(mo2_path: Optional[str] = None):
        mo2 = _ensure_mo2(mo2_path)
        mods_dir = mo2.mods_path
        if not mods_dir or not mods_dir.exists():
            raise HTTPException(status_code=404, detail="Mods directory not found")
        mods = [p.name for p in mods_dir.iterdir() if p.is_dir()]
        return ModsListResponse(mods=mods)

    @app.post("/api/mods/merge")
    def merge_mods(payload: MergeRequest):
        mo2 = _ensure_mo2(payload.mo2_path)
        mods_dir = mo2.mods_path
        if not mods_dir or not mods_dir.exists():
            raise HTTPException(status_code=404, detail="Mods directory not found")
        # placeholder: in future invoke merger
        merged = payload.mods
        return {"merged": merged, "status": "success"}

    # webhook for MO2
    @app.post("/api/webhook/mo2")
    def mo2_webhook(payload: WebhookRequest):
        mo2 = _ensure_mo2(payload.mo2_path)
        profile = payload.profile
        if profile not in mo2.list_profiles():
            raise HTTPException(status_code=404, detail=f"Profile '{profile}' not found")
        current_order = mo2.read_loadorder_txt(profile)
        if not current_order:
            raise HTTPException(status_code=404, detail="No plugins found in profile")
        issues = Fallout4Rules.validate_load_order(current_order)
        optimized = Fallout4Rules.optimize_load_order(current_order)
        return {
            "profile": profile,
            "issues": issues,
            "current_order": current_order,
            "optimized_order": optimized,
        }

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/health")
    def api_health(
        profile: Optional[str] = None,
        mo2_path: Optional[str] = None,
        run_ai: bool = True,
    ):
        """
        Run ``ModHealthChecker`` against the specified profile and return a
        scored health report (0–100).

        Query parameters
        ----------------
        profile : str
            MO2 profile name (required when mo2_path is supplied).
        mo2_path : str, optional
            Path to MO2 installation.  Auto-detected when omitted.
        run_ai : bool
            Set to ``false`` to skip the AI brain analysis (faster).
        """
        mo2 = None
        load_order: list = []
        if mo2_path or profile:
            try:
                mo2 = _ensure_mo2(mo2_path)
                if profile and profile in mo2.list_profiles():
                    load_order = mo2.read_loadorder_txt(profile)
            except HTTPException:
                pass

        if not load_order:
            raise HTTPException(
                status_code=400,
                detail="Provide profile + mo2_path (or auto-detect) to run a health check."
            )

        checker = ModHealthChecker(run_ai=run_ai)
        report = checker.check(load_order, profile=profile, mo2=mo2)
        return report.to_dict()

    # ── AI Brain endpoints ──────────────────────────────────────────────

    @app.post("/api/ai/analyze")
    def ai_analyze(payload: ConflictScanRequest):
        """
        Run a full AI brain analysis (conflict risk, anomalies, clusters,
        recommendations) on the specified MO2 profile.
        """
        mo2 = _ensure_mo2(payload.mo2_path)
        profile = payload.profile
        if not profile:
            raise HTTPException(status_code=400, detail="profile is required for AI analysis")
        if profile not in mo2.list_profiles():
            raise HTTPException(status_code=404, detail=f"Profile '{profile}' not found")

        load_order = mo2.read_loadorder_txt(profile)
        if not load_order:
            raise HTTPException(status_code=404, detail="No plugins found in profile")

        brain = ModAIBrain()
        return brain.full_analysis(load_order)

    @app.get("/api/ai/risk/{plugin_name}")
    def ai_risk(plugin_name: str):
        """Predict conflict-risk severity for a single plugin by name."""
        brain = ModAIBrain()
        return brain.predict_conflict_risk(plugin_name)

    @app.get("/api/ai/compatibility")
    def ai_compatibility(plugin_a: str, plugin_b: str):
        """Score compatibility between two plugins."""
        brain = ModAIBrain()
        score = brain.score_compatibility(plugin_a, plugin_b)
        return {
            "plugin_a": plugin_a,
            "plugin_b": plugin_b,
            "compatibility_score": score,
            "verdict": (
                "Likely compatible" if score >= 0.75
                else "May conflict — check manually" if score >= 0.4
                else "High conflict risk"
            ),
        }

    @app.post("/api/ai/fix")
    def ai_fix(payload: ConflictScanRequest):
        """
        Reason about a profile's load order and return complete fix scripts.

        Each entry in the response has ``filename``, ``fix_type``, ``code``,
        ``description``, and ``can_auto_apply``.
        """
        mo2 = _ensure_mo2(payload.mo2_path)
        profile = payload.profile
        if not profile:
            raise HTTPException(status_code=400, detail="profile is required")
        if profile not in mo2.list_profiles():
            raise HTTPException(status_code=404, detail=f"Profile '{profile}' not found")

        load_order = mo2.read_loadorder_txt(profile)
        if not load_order:
            raise HTTPException(status_code=404, detail="No plugins found in profile")

        reasoning = ModReasoner().reason_about_load_order(load_order)
        fixes = FixGenerator().generate_fixes(reasoning, load_order=load_order)

        return {
            "profile": profile,
            "reasoning_steps": len(reasoning.steps),
            "conclusion": reasoning.conclusion,
            "fixes": [f.to_dict() for f in fixes],
        }

    # Fallback index
    @app.get("/", include_in_schema=False)
    def index():
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return {"message": "Mossy Manager UI"}

    return app


app = build_app()
