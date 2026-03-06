# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Mossy Manager
Creates a standalone Windows executable that opens a self-contained desktop UI.

The built executable is intended to be placed in:
  <MO2 folder>\\tools\\MossyManager\\MossyManager.exe

Add it to MO2 Executables:
  Title    : Mossy Manager
  Binary   : <above path>
  Arguments: (leave blank)
  Start in : (leave blank)

See UI_MANIFEST (repository root) for the authoritative UI architecture spec.
DO NOT add uvicorn, fastapi, or webbrowser as the primary UI entry point —
the desktop GUI (tkinter) is the only interface launched by the executable.
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules

import os as _os

_spec_dir = _os.path.abspath(_os.path.dirname(__file__)) if '__file__' in globals() else _os.getcwd()

# ── Third-party packages that need full collection ──────────────────────────
_d_sklearn,  _b_sklearn,  _h_sklearn  = collect_all('sklearn')
_d_numpy,    _b_numpy,    _h_numpy    = collect_all('numpy')

block_cipher = None

a = Analysis(
    # Entry point: the GUI launcher (opens the desktop window directly)
    ['MossyManager_gui.py'],
    pathex=[_os.path.join(_spec_dir, 'src')],
    binaries=(
        _b_sklearn + _b_numpy
    ),
    datas=(
        [
            ('README.md',    '.'),
            ('LICENSE',      '.'),
            ('UI_MANIFEST',  '.'),
        ]
        + _d_sklearn
        + _d_numpy
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
            # ── Desktop GUI (tkinter) ──────────────────────────────────────
            'mossy_manager.gui',
            'mossy_manager.gui.app',
            'tkinter',
            'tkinter.ttk',
            'tkinter.messagebox',
            'tkinter.filedialog',
            'tkinter.font',
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
            # ── Standard library extras ───────────────────────────────────
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
            'threading',
            'dataclasses',
            'contextlib',
            'functools',
        ]
        + _h_sklearn
        + _h_numpy
    ),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        '_pytest',
        'setuptools',
        'pip',
        'torch',
        'tensorflow',
        'IPython',
        'ipykernel',
        'notebook',
        'matplotlib',
        # Web server stack is NOT included in the desktop executable
        'uvicorn',
        'fastapi',
        'starlette',
        'pydantic',
        'anyio',
        'h11',
        'httpx',
        'webbrowser',
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
    # windowed=True → no console window pops up alongside the GUI
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
