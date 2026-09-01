@echo off
cd /d "%~dp0"

set "PY="
where python >nul 2>nul
if not errorlevel 1 set "PY=python"

if not defined PY (
    where py >nul 2>nul
    if not errorlevel 1 set "PY=py"
)

if not defined PY (
    where python3 >nul 2>nul
    if not errorlevel 1 set "PY=python3"
)

if not defined PY (
    if exist "C:\Users\stk_gb\.workbuddy\binaries\python\versions\3.13.12\python.exe" set "PY=C:\Users\stk_gb\.workbuddy\binaries\python\versions\3.13.12\python.exe"
)

if not defined PY (
    echo.
    echo [ERROR] Python not found. Install Python and add it to PATH.
    echo Or double-click "一键推送.py" if .py is associated with python.exe.
    goto :PAUSE
)

echo Python found: %PY%
echo Running push script ...
echo.
%PY% "一键推送.py"

:PAUSE
echo.
echo ============================================
echo Finished. Press any key to close the window ...
pause >nul
