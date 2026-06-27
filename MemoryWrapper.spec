# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\main.py'],
    pathex=['.'],  # repo root, so the `src` package is importable
    binaries=[],
    datas=[('assets', 'assets')],
    hiddenimports=[
        'src',
        'src.settings',
        'src.logger',
        'src.core.signals',
        'src.core.utils',
        'src.dosbox.launcher',
        'src.dosbox.watcher',
        'src.report.parser',
        'src.report.generator',
        'src.ui.controller',
        'src.ui.preview_window',
        'src.ui.styles',
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
