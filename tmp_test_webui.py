import sys
from pathlib import Path
sys.path.append(r'D:/Mossy/Mossy-manager/src')
from fastapi.testclient import TestClient
import importlib
from mossy_manager.webui.app import app

class DummyMO2:
    def __init__(self, base):
        self.mo2_path = base
        self.mods_path = base / "mods"
        self._profile_dir = base / "profiles" / "Default"
        self.mods_path.mkdir(parents=True, exist_ok=True)
        self._profile_dir.mkdir(parents=True, exist_ok=True)
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

webapp = importlib.import_module('mossy_manager.webui.app')
fake = DummyMO2(Path('C:/temp/MO2fake'))
webapp._ensure_mo2 = lambda p=None: fake

c = TestClient(app)
print('POST status', c.post('/api/loadorder/optimize', json={'profile':'Default','apply':False,'backup':False}).status_code)
print('routes', [(r.path, getattr(r,'methods',None)) for r in app.routes])
