# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Mossy Manager
Creates a standalone executable for Windows distribution
"""

block_cipher = None

a = Analysis(
    ['src/mossy_manager/cli/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('README.md', '.'),
        ('LICENSE', '.'),
        ('src/mossy_manager/webui/static', 'mossy_manager/webui/static'),
    ],
    hiddenimports=[
        'mossy_manager',
        'mossy_manager.cli',
        'mossy_manager.cli.main',
        'mossy_manager.core',
        'mossy_manager.core.load_order',
        'mossy_manager.core.conflict_resolver',
        'mossy_manager.core.patcher',
        'mossy_manager.utils',
        'mossy_manager.utils.xedit_integration',
        'mossy_manager.games',
        'mossy_manager.games.fallout4',
        'mossy_manager.integrations',
        'mossy_manager.integrations.mo2',
        'mossy_manager.webui',
        'mossy_manager.webui.app',
        'fastapi',
        'uvicorn',
        'pydantic',
        'starlette',
        'click',
        'colorama',
        'tabulate',
        'yaml',
        'toml',
        'configparser',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'setuptools',
        'pip',
        '_pytest',
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
    icon=None,  # Add icon file path here if available
)
