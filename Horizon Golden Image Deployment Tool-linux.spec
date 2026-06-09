# -*- mode: python ; coding: utf-8 -*-
# Linux-specific spec — produces a COLLECT directory for distribution.

a = Analysis(
    ['horizon_golden_image_deployment_tool.py'],
    pathex=[],
    binaries=[],
    datas=[('logo.ico', '.')],
    hiddenimports=[
        'requests',
        'horizon_functions',
        'horizon_app',
        'keyring',
        'loguru',
        'PySide6.QtWidgets',
        'PySide6.QtCore',
        'PySide6.QtGui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    collect_all=['PySide6'],   # Qt plugins are not reliably auto-detected on Linux
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Horizon Golden Image Deployment Tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Horizon Golden Image Deployment Tool',
)
