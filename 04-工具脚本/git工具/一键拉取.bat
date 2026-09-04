@echo off
cd /d "%~dp0"

set "PY="

rem 1) WorkBuddy 管理版 Python 最优先（路径确定，绕开商店 stub）
if exist "%USERPROFILE%\.workbuddy\binaries\python\versions\3.13.12\python.exe" (
    set "PY=%USERPROFILE%\.workbuddy\binaries\python\versions\3.13.12\python.exe"
)

rem 2) PATH 上的 python / py / python3 —— 必须真跑通 --version 才采用（排除商店 stub）
if not defined PY (
    where python >nul 2>nul
    if not errorlevel 1 (
        python --version >nul 2>nul
        if not errorlevel 1 set "PY=python"
    )
)
if not defined PY (
    where py >nul 2>nul
    if not errorlevel 1 (
        py --version >nul 2>nul
        if not errorlevel 1 set "PY=py"
    )
)
if not defined PY (
    where python3 >nul 2>nul
    if not errorlevel 1 (
        python3 --version >nul 2>nul
        if not errorlevel 1 set "PY=python3"
    )
)

if not defined PY (
    echo.
    echo [ERROR] No working Python found. Install Python and add it to PATH.
    goto :PAUSE
)

echo Python found: %PY%
echo Running pull script ...
echo.
%PY% "一键拉取.py"
if errorlevel 1 (
    echo.
    echo [ERROR] Pull script exited with code %errorlevel%. See messages above.
)

:PAUSE
echo.
echo ============================================
echo Finished. Press any key to close the window ...
pause >nul
