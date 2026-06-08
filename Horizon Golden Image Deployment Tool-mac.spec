# -*- mode: python ; coding: utf-8 -*-
# Mac-specific spec — produces a self-contained .app bundle.

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
    collect_all=['PySide6'],
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
    upx=False,         # UPX is unreliable on macOS ARM/x86_64
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,  # None = native arch; set 'universal2' for fat binary
    codesign_identity=None,
    entitlements_file=None,
    icon='hgidt_logo.icns',
)

app = BUNDLE(
    exe,
    a.binaries,
    a.datas,
    name='Horizon Golden Image Deployment Tool.app',
    icon='hgidt_logo.icns',
    bundle_identifier='com.controlup.hgidt',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '11.0',
    },
)
