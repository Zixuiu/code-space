"""
macOS 风格 UI 主入口文件
"""
import sys
import os

if getattr(sys, 'frozen', False):
    current_dir = os.path.dirname(sys.executable)
else:
    current_dir = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, current_dir)

from app_macos import start_macos_app

if __name__ == "__main__":
    start_macos_app()