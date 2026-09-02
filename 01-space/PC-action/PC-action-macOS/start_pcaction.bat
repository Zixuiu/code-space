@echo off
REM ============================================================
REM  PC-action 一键启动脚本 (Windows)
REM  前提：已用 .venv 安装好 requirements.txt 全部依赖
REM  用法：双击本文件，或在命令行执行  start_pcaction.bat
REM ============================================================
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo [错误] 未找到 .venv 虚拟环境，请先运行：
    echo        ..\..\..\..\..\.. (在项目目录) python -m venv .venv
    echo        .venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)
echo 正在启动 PC-action ...
.venv\Scripts\python.exe run.py
pause
