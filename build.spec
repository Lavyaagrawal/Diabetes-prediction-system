# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Diabetes Prediction System
Creates a standalone Windows executable
"""

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('diabetes_app.kv', '.'),
        ('logo.png', '.'),
        ('model_data', 'model_data'),
    ],
    hiddenimports=[
        'kivy',
        'kivymd',
        'kivy.storage.jsonstore',
        'kivymd.uix',
        'kivymd.uix.dialog',
        'kivymd.uix.button',
        'kivymd.uix.boxlayout',
        'kivymd.uix.list',
        'kivymd.uix.menu',
        'kivymd.uix.textfield',
        'diabetes_chatbot',
        'joblib',
        'numpy',
        'requests',
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

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DiabetesPredictionApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True if you want to see console output for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one: 'logo.png'
)
