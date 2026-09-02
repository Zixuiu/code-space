# -*- coding: utf-8 -*-
"""
PC-action 无界面冒烟测试（headless / 服务器环境用）
目标：在不依赖真实显示器的前提下，验证所有模块能正常 import、
      QApplication 能创建、主窗口能构造，从而证明代码“能跑起来”。
运行：在 .venv 下执行  python smoke_test.py
"""
import os
import sys
import traceback

# 关键：在无显示器环境用 offscreen 平台插件，避免 "no Qt platform plugin" / 无显示错误
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def main():
    print("[smoke] 1/5 设置 Qt offscreen 平台 ...", flush=True)
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFont

    print("[smoke] 2/5 创建 QApplication ...", flush=True)
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)

    print("[smoke] 3/5 import 主模块 (app) ...", flush=True)
    import app  # noqa: F401  (确保 11k 行主模块能加载)

    print("[smoke] 4/5 import app_macos 并构造主窗口 ...", flush=True)
    from app_macos import MacOSAutoRecorderApp, start_macos_app  # noqa: F401
    from login_manager import LoginManager
    from utils import log_info

    print("[smoke] 5/5 构造 LoginManager + 主窗口(不进入事件循环) ...", flush=True)
    login_manager = LoginManager()
    win = MacOSAutoRecorderApp(login_manager=login_manager)
    win.setWindowFlags(Qt.FramelessWindowHint)
    win.show()
    win.hide()
    log_info("smoke test: 主窗口构造成功")
    print("[smoke] OK ✅ PC-action 模块导入与主窗口构造均无错误，代码可正常运行。", flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
