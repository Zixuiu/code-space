import io

bat = r'''@echo off
set "WB_NODE_DIR=C:\Users\stk_gb\.workbuddy\binaries\node\versions\22.22.2"
set "LOG=%~dp0freellmapi_start.log"

echo [%date% %time%] START > "%LOG%"
echo BAT: %~f0 >> "%LOG%"
echo cwd: %cd% >> "%LOG%"

where node >nul 2>nul
if errorlevel 1 set "PATH=%WB_NODE_DIR%;%PATH%"

echo [INFO] node: >> "%LOG%"
where node >> "%LOG%" 2>&1
echo [INFO] node version: >> "%LOG%"
node -v >> "%LOG%" 2>&1

if exist node_modules goto :skipinstall
echo [1/3] Installing dependencies... this may take a few minutes (better-sqlite3 native build)
echo [%date% %time%] npm install start >> "%LOG%"
call npm install >> "%LOG%" 2>&1
if errorlevel 1 goto :fail
echo [%date% %time%] npm install done >> "%LOG%"

:skipinstall
echo [2/3] Starting FreeLLMAPI Server on :3001 (new window)...
echo [%date% %time%] server start >> "%LOG%"
start "FreeLLMAPI-Server" cmd /k "npm run dev -w server"

echo [3/3] Waiting 15s for server, then auto-setup admin + keyless providers + print key...
echo [%date% %time%] waiting >> "%LOG%"
timeout /t 15 /nobreak >nul
echo [%date% %time%] bootstrap start >> "%LOG%"
node bootstrap.mjs >> "%LOG%" 2>&1
echo [%date% %time%] bootstrap end >> "%LOG%"

echo.
echo Done. Keep the FreeLLMAPI-Server window open to keep the proxy running.
echo Endpoint: http://127.0.0.1:3001/v1/chat/completions
echo Full log saved to: %LOG%
goto :showlog

:fail
echo.
echo [FAILED] npm install failed. Check %LOG% below.
echo If it says better-sqlite3 / node-gyp / MSBUILD, you need a C++ build toolchain,
echo or your network cannot reach GitHub to download the native package.

:showlog
echo.
echo ================= RUN LOG =================
type "%LOG%"
echo ================= END LOG =================
pause
'''

with io.open(r"D:\codespace\freellmapi\run_freellmapi2.bat", "w", encoding="utf-8", newline="\r\n") as f:
    f.write(bat)
print("written run_freellmapi2.bat")
