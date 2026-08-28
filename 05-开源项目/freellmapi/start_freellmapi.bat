@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM Locate Node.js: try system PATH, then WorkBuddy-managed runtime
set "WB_NODE_DIR=C:\Users\stk_gb\.workbuddy\binaries\node\versions\22.22.2"
where node >nul 2>nul
if errorlevel 1 (
  if exist "%WB_NODE_DIR%\node.exe" (
    set "PATH=%WB_NODE_DIR%;%PATH%"
    echo [INFO] Node.js not in PATH; using WorkBuddy-managed Node.
  ) else (
    echo [ERROR] Node.js not found. Install Node 20.18+ from https://nodejs.org then re-run.
    pause
    exit /b 1
  )
)

IF NOT EXIST node_modules (
  echo [1/3] Installing dependencies (first run, needs internet for native modules like better-sqlite3)...
  call npm install
  if errorlevel 1 (
    echo [ERROR] npm install failed. Check your internet / GitHub access, then retry.
    pause
    exit /b 1
  )
)

echo [2/3] Starting FreeLLMAPI Server on :3001 (new window)...
start "FreeLLMAPI-Server" cmd /k "npm run dev -w server"

echo [3/3] Waiting for server, then auto-setup admin + keyless providers + print API key...
node bootstrap.mjs

echo.
echo Done. Keep the FreeLLMAPI-Server window open to keep the proxy running.
echo Endpoint: http://127.0.0.1:3001/v1/chat/completions
pause
