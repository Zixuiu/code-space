@echo off
setlocal
set "WB_NODE_DIR=C:\Users\stk_gb\.workbuddy\binaries\node\versions\22.22.2"
set "PATH=%WB_NODE_DIR%;%PATH%"
set "ROOT=%~dp0"
cd /d "%ROOT%server"
powershell -NoProfile -Command "Start-Process -FilePath '%WB_NODE_DIR%\node.exe' -ArgumentList 'dist/index.js' -WorkingDirectory '%ROOT%server' -WindowStyle Hidden -RedirectStandardOutput '%ROOT%freellmapi_server.log' -RedirectStandardError '%ROOT%freellmapi_server.err'"
echo FreeLLMAPI started (hidden). Log: %ROOT%freellmapi_server.log
