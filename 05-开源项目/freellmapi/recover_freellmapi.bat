@echo off
setlocal
set "WB_NODE_DIR=C:\Users\stk_gb\.workbuddy\binaries\node\versions\22.22.2"
set "PATH=%WB_NODE_DIR%;%PATH%"
set "ROOT=%~dp0"
echo === recover_freellmapi.bat : 恢复免费 API 后端 ===
echo.
echo [1/5] 生成 server/.env (ENCRYPTION_KEY) ...
if exist "%ROOT%server\.env" goto :have_env
powershell -NoProfile -Command "$k=([BitConverter]::ToString((1..32|%%{Get-Random -Maximum 256})) -replace '-',''); Set-Content -Path '%ROOT%server\.env' -Value "ENCRYPTION_KEY=$k`nPORT=3001`nNODE_ENV=production" -Encoding utf8"
goto :after_env
:have_env
echo .env 已存在，跳过生成
:after_env
echo.
echo [2/5] npm install (重建 better-sqlite3 原生模块，约 5-10 分钟) ...
cd /d "%ROOT%server"
call npm install --no-audit --no-fund
echo.
echo [3/5] npm run build (tsc -> dist) ...
call npm run build
echo.
echo [4/5] 重置数据库以便重新引导 (旧 key 将失效，会生成新 key) ...
if exist "%ROOT%server\data\freeapi.db" del "%ROOT%server\data\freeapi.db"
echo.
echo [5/5] 启动服务 (后台隐藏运行) ...
taskkill /IM node.exe /F
timeout /t 2 /nobreak >nul
powershell -NoProfile -Command "Start-Process -FilePath '%WB_NODE_DIR%\node.exe' -ArgumentList 'dist/index.js' -WorkingDirectory '%ROOT%server' -WindowStyle Hidden -RedirectStandardOutput '%ROOT%freellmapi_server.log' -RedirectStandardError '%ROOT%freellmapi_server.err'"
timeout /t 15 /nobreak >nul
cd /d "%ROOT%"
node bootstrap.mjs
echo.
echo === 完成。服务日志: %ROOT%freellmapi_server.log ===
echo === 上面的 Unified API Key 就是新的免费端点密钥 ===
