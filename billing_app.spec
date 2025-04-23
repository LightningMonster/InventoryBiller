# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT, Tree

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'tkcalendar',
        'reportlab',
        'reportlab.lib',
        'reportlab.pdfgen',
        'reportlab.platypus',
        'reportlab.lib.styles',
        'reportlab.lib.pagesizes',
        'reportlab.lib.units',
        'sqlite3',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Include additional files
a.datas += [
    ('storage.db', './storage.db', 'DATA'),
    # Add your app icon if you have one
    # ('logo.ico', 'path/to/logo.ico', 'DATA'),
]

# Add directories
try:
    a.datas += Tree('./bills', prefix='bills')
except FileNotFoundError:
    import os
    # Create bills directory if it doesn't exist
    os.makedirs('./bills', exist_ok=True)
    a.datas += Tree('./bills', prefix='bills')

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BillingApp',
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
    icon=None,  # Add your icon here if you have one: 'path/to/icon.ico'
)