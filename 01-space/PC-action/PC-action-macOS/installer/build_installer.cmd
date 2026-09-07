@echo off
REM ============================================================
REM PC-Action 一键构建安装包
REM 步骤：1) 用 PyInstaller 重新打包 exe  2) 用 Inno Setup 打成安装包
REM 前置：a) 已安装 Inno Setup 6   b) venv 里装有 pyinstaller
REM 用法：在 installer 目录执行  build_installer.cmd
REM ============================================================
setlocal

REM 进入项目根目录（本脚本所在目录的上级）
cd /d "%~dp0.."
set ROOT=%CD%
set VENV=%ROOT%\.venv\Scripts

echo [1/2] PyInstaller 打包 exe ...
"%VENV%\python.exe" -m PyInstaller --clean -y PC-Action.spec
if errorlevel 1 (
  echo 打包失败：请确认 venv 已安装 pyinstaller
  exit /b 1
)

echo [2/2] Inno Setup 生成安装包 ...
set ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" set ISCC=C:\Program Files\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" (
  echo 未找到 ISCC.exe，请先安装 Inno Setup 6，或修改本脚本中的 ISCC 路径
  exit /b 1
)
"%ISCC%" "%ROOT%\installer\setup.iss"
if errorlevel 1 (
  echo Inno Setup 打包失败
  exit /b 1
)

echo.
echo 完成！安装包位于：%ROOT%\installer\output\PC-Action-Setup.exe
endlocal