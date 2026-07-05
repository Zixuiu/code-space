# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

a = Analysis(
    ['D:\\code空间\\01-开发项目\\PC-action\\PC-action-macOS\\main.py'],
    pathex=['D:\\code空间\\01-开发项目\\PC-action\\PC-action-macOS'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PyQt5',
        'PyQt5.QtWidgets',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtSvg',
        'cv2',
        'numpy',
        'PIL',
        'PIL.Image',
        'PIL.ImageGrab',
        'keyboard',
        'pyautogui',
        'mss',
        'supabase',
        'pynput',
        'pynput.keyboard',
        'pynput.mouse',
        'pygetwindow',
        'pyperclip',
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
    name='PC-action-macOS',
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
