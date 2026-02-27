# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Mossy Manager
Creates a standalone executable for Windows distribution

Uses collect_all() for packages with many lazy sub-imports (sklearn, numpy,
fastapi, starlette, pydantic, anyio) so the bundled exe works at 100% out of
the box — no separate Python installation required.
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules

import os as _os

# Determine spec directory even when __file__ is missing (PyInstaller+Python 3.14 issue)
_spec_dir = _os.path.abspath(_os.path.dirname(__file__)) if '__file__' in globals() else _os.getcwd()

# ── Third-party packages that need full collection ─────────────────────────
# sklearn has hundreds of lazy sub-imports PyInstaller cannot detect statically
_d_sklearn,  _b_sklearn,  _h_sklearn  = collect_all('sklearn')
_d_numpy,    _b_numpy,    _h_numpy    = collect_all('numpy')
_d_fastapi,  _b_fastapi,  _h_fastapi  = collect_all('fastapi')
_d_starlette,_b_starlette,_h_starlette= collect_all('starlette')
_d_pydantic, _b_pydantic, _h_pydantic = collect_all('pydantic')
_d_anyio,    _b_anyio,    _h_anyio    = collect_all('anyio')
_h_uvicorn                            = collect_submodules('uvicorn')

block_cipher = None

a = Analysis(
    ['src/mossy_manager/cli/main.py'],
    # ── pathex must include src/ so mossy_manager package is found ──────────
    pathex=[_os.path.join(_spec_dir, 'src')],
    binaries=(
        _b_sklearn + _b_numpy + _b_fastapi + _b_starlette + _b_pydantic + _b_anyio
    ),
    datas=(
        [
            ('README.md', '.'),
            ('LICENSE', '.'),
            # Web UI static assets (loaded at runtime by FastAPI StaticFiles)
            ('src/mossy_manager/webui/static', 'mossy_manager/webui/static'),
        ]
        + _d_sklearn
        + _d_numpy
        + _d_fastapi
        + _d_starlette
        + _d_pydantic
        + _d_anyio
    ),
    hiddenimports=(
        [
            # ── All mossy_manager modules ──────────────────────────────────
            'mossy_manager',
            'mossy_manager.main',
            'mossy_manager.mod_manager',
            'mossy_manager.profile_manager',
            'mossy_manager.config_manager',
            'mossy_manager.cli',
            'mossy_manager.cli.main',
            'mossy_manager.core',
            'mossy_manager.core.load_order',
            'mossy_manager.core.conflict_resolver',
            'mossy_manager.core.patcher',
            'mossy_manager.core.dependency_graph',
            'mossy_manager.games',
            'mossy_manager.games.fallout4',
            'mossy_manager.integrations',
            'mossy_manager.integrations.mo2',
            'mossy_manager.utils',
            'mossy_manager.utils.xedit_integration',
            'mossy_manager.utils.backup_manager',
            'mossy_manager.utils.health_checker',
            'mossy_manager.utils.ini_patcher',
            'mossy_manager.ai',
            'mossy_manager.ai.brain',
            'mossy_manager.ai.fix_generator',
            'mossy_manager.ai.reasoner',
            'mossy_manager.ai.script_writer',
            'mossy_manager.webui',
            'mossy_manager.webui.app',
            # ── CLI / formatting ──────────────────────────────────────────
            'click',
            'colorama',
            'colorama.ansi',
            'colorama.ansitowin32',
            'colorama.initialise',
            'colorama.winterm',
            'tabulate',
            # ── Configuration / serialisation ─────────────────────────────
            'yaml',
            'toml',
            'configparser',
            'json',
            # ── uvicorn (ASGI server for the web UI) ──────────────────────
            'uvicorn',
            'uvicorn.logging',
            'uvicorn.loops',
            'uvicorn.loops.auto',
            'uvicorn.loops.asyncio',
            'uvicorn.protocols',
            'uvicorn.protocols.http',
            'uvicorn.protocols.http.auto',
            'uvicorn.protocols.http.h11_impl',
            'uvicorn.protocols.websockets',
            'uvicorn.protocols.websockets.auto',
            'uvicorn.lifespan',
            'uvicorn.lifespan.off',
            # ── h11 (HTTP/1.1 library used by uvicorn) ────────────────────
            'h11',
            'h11._readers',
            'h11._writers',
            'h11._events',
            'h11._connection',
            'h11._headers',
            'h11._receivebuffer',
            'h11._state',
            'h11._util',
            # ── Standard library extras sometimes missed by PyInstaller ───
            'email.mime.text',
            'email.mime.multipart',
            'email.mime.base',
            'logging.handlers',
            'importlib.metadata',
            'importlib.resources',
            'typing_extensions',
            'pathlib',
            'shutil',
            'subprocess',
            'webbrowser',
            'dataclasses',
            'contextlib',
            'functools',
        ]
        + _h_sklearn
        + _h_numpy
        + _h_fastapi
        + _h_starlette
        + _h_pydantic
        + _h_anyio
        + _h_uvicorn
    ),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        '_pytest',
        'setuptools',
        'pip',
        'torch',       # optional sklearn dep — not installed / not needed
        'tensorflow',
        'IPython',
        'ipykernel',
        'notebook',
        'matplotlib',
        'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MossyManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
