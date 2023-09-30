# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['horizon_golden_image_deployment_tool.py'],
    pathex=[],
    binaries=[],
    datas=[('logo.ico', '.')],
    hiddenimports=['requests,tkcalendar,horizon_functions.py,tkinter.tk,tkinter.ttk,tkinter,simpledialog,tktooltip.tooltip,tkcalendar.dateentry,datetime.datetime,datetime.time,datetime.time,babel.dates,babel.core,babel.localedata,babel.numbers,loguru'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='hgidt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['hgidt_logo.icns'],
)
app = BUNDLE(
    exe,
    name='hgidt.app',
    icon='hgidt_logo.icns',
    bundle_identifier=None,
)
