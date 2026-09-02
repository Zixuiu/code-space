@echo off
REM ============================================================
REM  手机无线投屏助手（免敲 adb）
REM  双击本文件即可启动 GUI；按窗口提示填写手机无线调试信息
REM  依赖：同目录的 adb.exe / scrcpy.exe，以及 PyQt5（复用 PC-action 的 venv）
REM ============================================================
cd /d "%~dp0"

REM 优先用 PC-action 的 venv（已装 PyQt5）；找不到则退回系统 python
set VENV_PY=..\PC-action\PC-action-macOS\.venv\Scripts\python.exe
if exist "%VENV_PY%" (
    "%VENV_PY%" wifi_mirror.py
) else (
    python wifi_mirror.py
)
