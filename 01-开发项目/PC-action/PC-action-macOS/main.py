"""
macOS 风格 UI 主入口文件
"""
import sys
import os

# DPI 感知仅在打包后的 exe 中设置，保持开发版原版行为一致
if sys.platform == 'win32' and getattr(sys, 'frozen', False):
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

if getattr(sys, 'frozen', False):
    current_dir = os.path.dirname(sys.executable)
else:
    current_dir = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, current_dir)

from app_macos import start_macos_app

if __name__ == "__main__":
    start_macos_app()