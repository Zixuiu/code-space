@echo off
chcp 65001 >nul
echo 正在打包PC-action应用程序...

REM 检查是否安装了PyInstaller
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo 正在安装PyInstaller...
    pip install pyinstaller
)

REM 检查是否存在spec文件
if not exist "resent\PC-action.spec" (
    echo 错误: 找不到PC-action.spec文件
    pause
    exit /b 1
)

echo 开始打包过程...
cd resent
pyinstaller "PC-action.spec"

if errorlevel 1 (
    echo 打包过程中出现错误
    pause
    exit /b 1
)

echo.
echo 打包完成！
echo 可执行文件位于: %~dp0resent\dist\PC-action.exe
echo.
echo 按任意键复制到桌面...
pause >nul

REM 复制到桌面
copy "dist\PC-action.exe" "%USERPROFILE%\Desktop\PC-action.exe"

echo 已将PC-action.exe复制到桌面
echo.
pause