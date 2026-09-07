# -*- mode: python ; coding: utf-8 -*-
"""
PC-Action 安装包专用打包脚本（onedir 模式）

产物：dist\\PC-Action\\PC-Action.exe  （同目录带 _internal 依赖）
用途：交给 installer\\setup.nsi 打成真正的安装包（用户可自选安装位置）

构建命令（项目根目录执行）：
    .venv\\Scripts\\python.exe -m PyInstaller --clean --noconfirm PC-Action-install.spec
"""

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icons', 'icons'),                 # 图标资源（load_svg_icon 按 __file__/icons 定位）
        ('pricing.json', '.'),              # 定价配置（entitlement.get_pricing 按 __file__ 定位）
        ('data', 'data'),                   # 组合技能等默认数据
    ],
    hiddenimports=[
        'pynput.keyboard._win32',           # pynput 动态加载的平台后端
        'pynput.mouse._win32',
        'keyboard',
        'supabase',
        'cv2',
        'mss',
        'pyautogui',
        'requests',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'unittest',
        'pytest',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PC-Action',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
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
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='PC-Action',
)
