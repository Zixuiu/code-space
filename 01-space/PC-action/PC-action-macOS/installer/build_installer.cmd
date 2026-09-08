@echo off
chcp 65001 >nul
REM ============================================================
REM  PC-Action 一键构建安装包（NSIS 版，无需安装任何打包工具）
REM
REM  步骤：
REM    1) 生成图标 installer\app.ico（如已存在则跳过）
REM    2) PyInstaller 打包  ..\dist\Action\Action.exe
REM    3) NSIS 编译安装包   installer\output\Action-<版本>-Setup.exe
REM
REM  前置：.venv 里已装 pyinstaller
REM        .venv\Scripts\python.exe -m pip install pyinstaller
REM
REM  用法：双击本文件，或在 installer 目录执行 build_installer.cmd
REM        指定版本：build_installer.cmd 1.0.1
REM ============================================================
setlocal

cd /d "%~dp0.."
set ROOT=%CD%
set VENV=%ROOT%\.venv\Scripts\python.exe
set NSIS=%~dp0tools\nsis\nsis-3.10\makensis.exe

if "%~1"=="" (set APPVER=1.0.0) else (set APPVER=%~1)

if not exist "%VENV%" (
  echo [错误] 未找到虚拟环境：%VENV%
  pause
  exit /b 1
)

REM ---- 0) NSIS 编译器缺失时自动下载便携版 ----
if not exist "%NSIS%" (
  echo [0/3] 未找到 NSIS，正在下载便携版 ...
  powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$zip='%~dp0tools\nsis.zip'; New-Item -ItemType Directory -Force -Path '%~dp0tools' ^| Out-Null; ^
     [Net.ServicePointManager]::SecurityProtocol='Tls12'; ^
     Invoke-WebRequest -Uri 'https://sourceforge.net/projects/nsis/files/NSIS%%203/3.10/nsis-3.10.zip/download' -OutFile $zip -UseBasicParsing; ^
     Expand-Archive -Path $zip -DestinationPath '%~dp0tools\nsis' -Force"
  if not exist "%NSIS%" (
    echo [错误] NSIS 下载/解压失败，请手动下载后放到 tools\nsis\nsis-3.10\
    pause
    exit /b 1
  )
)

REM ---- 1) 图标 ----
if not exist "%~dp0app.ico" (
  echo [1/3] 生成图标 app.ico ...
  "%VENV%" "%~dp0make_icon.py"
) else (
  echo [1/3] 图标已存在，跳过
)

REM ---- 2) PyInstaller 打包 ----
echo [2/3] PyInstaller 打包中（约 2-5 分钟）...
"%VENV%" -m PyInstaller --clean --noconfirm PC-Action-install.spec
if errorlevel 1 (
  echo [错误] PyInstaller 打包失败
  pause
  exit /b 1
)

REM ---- 3) 计算所需空间并编译安装包 ----
set DISTDIR=%ROOT%\dist\Action
if not exist "%DISTDIR%\Action.exe" (
  echo [错误] 未找到打包产物：%DISTDIR%\PC-Action.exe
  pause
  exit /b 1
)

for /f %%i in ('powershell -NoProfile -Command "$s=(Get-ChildItem -LiteralPath '%DISTDIR%' -Recurse -File ^| Measure-Object -Property Length -Sum).Sum; [int]($s/1MB)+60"') do set REQMB=%%i
echo     打包体积约 %REQMB% MB

echo [3/3] NSIS 编译安装包（压缩中，请稍候）...
"%NSIS%" /V2 /DAPP_VERSION=%APPVER% /DREQUIRED_MB=%REQMB% "%~dp0setup.nsi"
if errorlevel 1 (
  echo [错误] NSIS 编译失败
  pause
  exit /b 1
)

echo.
echo 完成！安装包：%~dp0output\Action-%APPVER%-Setup.exe
echo.
pause
endlocal
