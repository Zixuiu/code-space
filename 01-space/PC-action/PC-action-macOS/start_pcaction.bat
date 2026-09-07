@echo off
REM ============================================================
REM  PC-action 一键启动脚本 (Windows)
REM  前提：已用 .venv 安装好 requirements.txt 全部依赖
REM  用法：双击本文件，或在命令行执行  start_pcaction.bat
REM
REM  ★ 说明：本脚本会自动以「管理员权限」启动项目。
REM  原因：流程快捷键依赖 keyboard 库的 Windows 全局键盘钩子，
REM        在普通权限下该钩子会偶发丢失按键（导致「按了没反应」），
REM        以管理员运行后全局钩子稳定，随机失效基本消失。
REM ============================================================
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [错误] 未找到 .venv 虚拟环境，请先运行：
    echo        python -m venv .venv
    echo        .venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

REM ---- 检测是否已是管理员：net session 需要管理员权限，失败则非管理员 ----
net session >nul 2>&1
if %errorlevel% EQU 0 (
    echo 已以管理员身份运行，正在启动 PC-action ...
    ".venv\Scripts\python.exe" run.py
    pause
) else (
    echo 检测到普通权限，正在请求管理员权限（Windows 会弹出 UAC 确认框）...
    echo 若点击「否」则以普通权限运行，快捷键可能偶发失效。
    powershell -NoProfile -Command "Start-Process -FilePath '%~dp0.venv\Scripts\python.exe' -ArgumentList 'run.py' -WorkingDirectory '%~dp0' -Verb RunAs"
    if errorlevel 1 (
        echo.
        echo [提示] 管理员授权被取消，退回到普通权限运行 ...
        ".venv\Scripts\python.exe" run.py
        pause
    ) else (
        echo 已以管理员权限启动 PC-action，本窗口可以关闭。
    )
)