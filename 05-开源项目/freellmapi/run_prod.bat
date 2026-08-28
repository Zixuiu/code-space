@echo off
setlocal
set "WB_NODE_DIR=C:\Users\stk_gb\.workbuddy\binaries\node\versions\22.22.2"
set "PATH=%WB_NODE_DIR%;%PATH%"
set "ROOT=%~dp0"

echo === run_prod.bat : FreeLLMAPI production mode ===
echo.
echo [1/4] building server (tsc -> dist)...
cd /d "%ROOT%server"
call npm run build
if errorlevel 1 (
  echo [WARN] build failed; will use existing dist if present
  if not exist "dist\index.js" goto :buildfail
)

echo [2/4] stopping any running dev/old server (node.exe)...
taskkill /IM node.exe /F
timeout /t 3 /nobreak >nul

echo [3/4] starting production server (node dist/index.js, hidden)...
cd /d "%ROOT%server"
powershell -NoProfile -Command "Start-Process -FilePath '%WB_NODE_DIR%\node.exe' -ArgumentList 'dist/index.js' -WorkingDirectory '%ROOT%server' -WindowStyle Hidden -RedirectStandardOutput '%ROOT%freellmapi_server.log' -RedirectStandardError '%ROOT%freellmapi_server.err'"

echo [4/4] waiting 15s for server, then auto-setup admin + keyless + print key...
cd /d "%ROOT%"
timeout /t 15 /nobreak >nul
node bootstrap.mjs

echo.
echo === done. server log: %ROOT%freellmapi_server.log ===
echo === server runs hidden in background; close this window anytime ===
pause
goto :eof

:buildfail
echo [FAILED] npm run build failed and no dist/index.js present - see output above
pause
