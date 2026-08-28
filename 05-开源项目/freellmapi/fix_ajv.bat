@echo off
setlocal
set "ROOT=%~dp0"
echo === fix_ajv.bat ===
echo.
echo [1/3] closing any leftover node processes (tsx watch)...
taskkill /IM node.exe /F
echo.
echo [2/3] removing broken server\node_modules\ajv folder...
if exist "%ROOT%server\node_modules\ajv" goto :do_rmdir
goto :after_rmdir
:do_rmdir
rmdir /s /q "%ROOT%server\node_modules\ajv"
:after_rmdir
echo.
echo [3/3] reinstalling ajv in server/ (fresh download, ~30s)...
cd /d "%ROOT%server"
call npm install ajv --no-audit --no-fund
echo.
echo === done. now close this window and re-run run_freellmapi2.bat ===
pause
