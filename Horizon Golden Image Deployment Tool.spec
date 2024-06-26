# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['horizon_golden_image_deployment_tool.py'],
    pathex=[],
    binaries=[],
    datas=[('logo.ico', '.')],
    hiddenimports=['requests,tkcalendar,horizon_functions.py,tkinter.tk,tkinter.ttk,tkinter,tkcalendar.dateentry,datetime.datetime,datetime.time,datetime.time,babel.dates,babel.core,babel.localedata,babel.numbers,loguru'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    icon=['logo.ico'],
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
