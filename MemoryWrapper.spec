# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\main.py'],
    pathex=['src'],  # src on the path: modules import as top-level (settings, factory, ...)
    binaries=[],
    datas=[('assets', 'assets')],
    hiddenimports=[
        'factory',
        'settings',
        'logger',
        'core.signals',
        'core.utils',
        'dosbox.launcher',
        'dosbox.watcher',
        'report.parser',
        'report.generator',
        'report.naming',
        'ui.controller',
        'ui.preview_window',
        'ui.styles',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MemoryWrapper',
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
    icon=['assets\\icon.ico'],
)
