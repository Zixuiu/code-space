"""
PC-action 启动脚本 (Windows)
自动设置 Qt 插件路径，避免 "no Qt platform plugin" 错误。
用法: python run.py
"""
import os
import sys

# 确保 Qt 能找到平台插件（qwindows.dll）
import PyQt5
_plugin = os.path.join(PyQt5.__path__[0], 'Qt5', 'plugins')
os.environ.setdefault('QT_QPA_PLATFORM_PLUGIN_PATH', _plugin)
os.environ.setdefault('QT_PLUGIN_PATH', _plugin)

# DPI 感知
if sys.platform == 'win32':
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

from app_macos import start_macos_app

if __name__ == '__main__':
    start_macos_app()
