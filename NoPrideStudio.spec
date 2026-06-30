# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['studio.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('pikcher/23icon/*.png', 'pikcher/23icon'), 
        ('pikcher/metadata.json', 'pikcher'),
        ('texconv.exe', '.'),
        ('repak.exe', '.'),
        ('dds_tools/', 'dds_tools'),
        ('original_icons/', 'original_icons'),
        ('extracted/', 'extracted')
    ],
    hiddenimports=[],
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
    name='NoPrideStudio',
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
)
