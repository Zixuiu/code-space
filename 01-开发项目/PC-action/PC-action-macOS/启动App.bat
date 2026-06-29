@echo off
chcp 65001 >nul
title PC-action macOS风格应用

echo ============================================
echo   正在启动 PC-action 应用...
echo ============================================
echo.

set "APP_DIR=d:\code空间\01-开发项目\PC-action\PC-action-macOS"

if not exist "%APP_DIR%\main.py" (
    echo [错误] 找不到应用文件！
    echo 请检查路径是否正确：%APP_DIR%
    pause
    exit /b 1
)

cd /d "%APP_DIR%"
python main.py

if errorlevel 1 (
    echo.
    echo [错误] 启动失败！请检查 Python 是否已安装。
    pause
)