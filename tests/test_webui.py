"""Tests for the FastAPI web UI endpoints."""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from mossy_manager.webui.app import app, build_app


class DummyMO2:
    def __init__(self, base: Path):
        self.mo2_path = base
        self.mods_path = base / "mods"
        self._profile_dir = base / "profiles" / "Default"
        self.mods_path.mkdir(parents=True, exist_ok=True)
        self._profile_dir.mkdir(parents=True, exist_ok=True)
        # create minimal plugin files
        (self._profile_dir / "plugins.txt").write_text("*A.esm\n")
        (self._profile_dir / "loadorder.txt").write_text("A.esm\n")

    def list_profiles(self):
        return ["Default"]

    def read_loadorder_txt(self, profile):
        return ["A.esm"]

    def read_plugins_txt(self, profile):
        return {"A.esm": True}

    def get_profile_path(self, profile):
        return self._profile_dir

    def write_plugins_txt(self, profile, plugins):
        self.written_plugins = plugins

    def write_loadorder_txt(self, profile, order):
        self.written_order = order


class DummyResolver:
    def __init__(self, mods_path):
        pass

    def scan_mod_files(self, name, path):
        pass

    def generate_report(self):
        return {"dummy": True}

    def get_statistics(self):
        return {"total_conflicts": 1, "critical": 0, "high": 1, "medium": 0, "low": 0}

    def export_for_xedit(self):
        return []


class DummyXEdit:
    def __init__(self, xedit_path=None):
        self.called = False

    def create_conflict_resolution_patch(self, conflicts, patch_name, output_dir):
        self.called = True
        return {"success": True, "export_path": "foo.pat", "script_path": "bar.pas", "xedit_launched": False}


import importlib

@pytest.fixture(autouse=True)
def patch_mo2_and_tools(tmp_path, monkeypatch):
    """Provide a fake MO2 installation and substitute resolver/xedit classes."""
    fake = DummyMO2(tmp_path / "MO2")
    webapp = importlib.import_module("mossy_manager.webui.app")
    # disable static mount by pointing to non-existent directory before building
    monkeypatch.setattr(webapp, "static_dir", Path("/does/not/exist"))
    monkeypatch.setattr(webapp, "_ensure_mo2", lambda p=None: fake)
    monkeypatch.setattr(webapp, "ConflictResolver", DummyResolver)
    monkeypatch.setattr(webapp, "XEditIntegration", DummyXEdit)
    # rebuild app so static files are not mounted
    global_test_app = build_app()
    # expose a client factory if needed
    return fake


def test_optimize_basic(monkeypatch):
    """Optimizing without any extra flags returns expected structure."""
    test_app = build_app()
    client = TestClient(test_app)

    payload = {"profile": "Default", "apply": False, "backup": False}
    res = client.post("/api/loadorder/optimize", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["profile"] == "Default"
    assert data["issues"]
    assert "optimized_order" in data
    assert data["applied"] is False
    assert "recommendations" in data


def test_optimize_with_conflicts():
    """Requesting a conflict scan adds report/stats to response."""
    test_app = build_app()
    client = TestClient(test_app)
    payload = {"profile": "Default", "apply": False, "backup": False, "scan_conflicts": True}
    res = client.post("/api/loadorder/optimize", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data.get("conflict_report") == {"dummy": True}
    assert data.get("conflict_stats")["high"] == 1
    assert "recommendations" in data


def test_optimize_with_xedit_and_patch():
    """resolve_xedit flag should invoke XEditIntegration and return its result."""
    test_app = build_app()
    client = TestClient(test_app)
    payload = {
        "profile": "Default",
        "apply": False,
        "backup": False,
        "scan_conflicts": True,
        "resolve_xedit": True,
        "patch_name": "MyPatch",
        "xedit_path": "C:/xedit.exe",
    }
    res = client.post("/api/loadorder/optimize", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data.get("xedit_result")["export_path"] == "foo.pat"
    assert data.get("xedit_result")["script_path"] == "bar.pas"


def test_conflict_scan_endpoint():
    test_app = build_app()
    client = TestClient(test_app)
    res = client.post("/api/conflicts/scan", json={})
    assert res.status_code == 200
    data = res.json()
    assert data["scanned_mods"] == 0 or data["scanned_mods"] >= 0
    assert "stats" in data


def test_version_endpoint():
    test_app = build_app()
    client = TestClient(test_app)
    res = client.get("/api/version")
    assert res.status_code == 200
    data = res.json()
    assert "current" in data
    assert "update_available" in data


def test_mods_and_merge(tmp_path, monkeypatch):
    # replicate fixture logic to patch MO2, resolver, xedit
    fake = DummyMO2(tmp_path / "MO2")
    import importlib
    webapp = importlib.import_module("mossy_manager.webui.app")
    monkeypatch.setattr(webapp, "static_dir", Path("/does/not/exist"))
    monkeypatch.setattr(webapp, "_ensure_mo2", lambda p=None: fake)
    monkeypatch.setattr(webapp, "ConflictResolver", DummyResolver)
    monkeypatch.setattr(webapp, "XEditIntegration", DummyXEdit)
    test_app = build_app()
    client = TestClient(test_app)
    # mods directory initially empty
    res = client.get("/api/mods")
    assert res.status_code == 200
    assert res.json()["mods"] == []
    # create some mods
    mp = fake.mods_path
    (mp / "ModA").mkdir()
    (mp / "ModB").mkdir()
    res = client.get("/api/mods")
    assert set(res.json()["mods"]) == {"ModA", "ModB"}
    # merge request
    res = client.post("/api/mods/merge", json={"mods": ["ModA", "ModB"]})
    assert res.status_code == 200
    data = res.json()
    assert data["merged"] == ["ModA", "ModB"]


def test_webhook_optimize(tmp_path, monkeypatch):
    fake = DummyMO2(tmp_path / "MO2")
    import importlib
    webapp = importlib.import_module("mossy_manager.webui.app")
    monkeypatch.setattr(webapp, "static_dir", Path("/does/not/exist"))
    monkeypatch.setattr(webapp, "_ensure_mo2", lambda p=None: fake)
    monkeypatch.setattr(webapp, "ConflictResolver", DummyResolver)
    monkeypatch.setattr(webapp, "XEditIntegration", DummyXEdit)
    # add profile
    profdir = fake.mo2_path / "profiles" / "Default"
    profdir.mkdir(parents=True, exist_ok=True)
    (profdir / "loadorder.txt").write_text("A.esp\n")
    (profdir / "plugins.txt").write_text("A.esp\n")
    test_app = build_app()
    client = TestClient(test_app)
    res = client.post("/api/webhook/mo2", json={"profile":"Default"})
    assert res.status_code == 200
    data = res.json()
    assert data["profile"] == "Default"
    assert "optimized_order" in data


def test_ui_persistence_code_present():
    # ensure index.html contains localStorage logic for state
    idx = Path(__file__).parent.parent / "src" / "mossy_manager" / "webui" / "static" / "index.html"
    text = idx.read_text()
    assert "localStorage.setItem" in text
    assert "localStorage.getItem" in text


def test_progress_stream(tmp_path, monkeypatch):
    """Verify SSE broadcaster sends messages to connected queue clients."""
    import importlib
    import queue as stdlib_queue

    webapp = importlib.import_module("mossy_manager.webui.app")

    # 1. Unit-test send_progress: attach a real Queue, broadcast, verify receipt
    test_q: stdlib_queue.Queue = stdlib_queue.Queue(maxsize=10)
    webapp._stream_clients.append(test_q)
    try:
        webapp.send_progress("hello")
        msg = test_q.get(timeout=1.0)
        assert msg == "hello"
    finally:
        if test_q in webapp._stream_clients:
            webapp._stream_clients.remove(test_q)

    # 2. Verify full-queue messages are silently dropped (no exception)
    full_q: stdlib_queue.Queue = stdlib_queue.Queue(maxsize=1)
    full_q.put("already_full")
    webapp._stream_clients.append(full_q)
    try:
        webapp.send_progress("overflow")   # must not raise
    finally:
        if full_q in webapp._stream_clients:
            webapp._stream_clients.remove(full_q)

    # 3. Smoke-test: /api/stream route is registered in the built app
    monkeypatch.setattr(webapp, "static_dir", Path("/does/not/exist"))
    monkeypatch.setattr(webapp, "_ensure_mo2", lambda p=None: DummyMO2(tmp_path / "MO2"))
    test_app = build_app()
    route_paths = [getattr(r, "path", None) for r in test_app.routes]
    assert "/api/stream" in route_paths
