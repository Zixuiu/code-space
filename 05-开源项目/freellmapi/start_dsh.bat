@echo off
set "WB_NODE_DIR=C:\Users\stk_gb\.workbuddy\binaries\node\versions\22.22.2"
set "PY=C:\Users\stk_gb\.workbuddy\binaries\python\versions\3.13.12\python.exe"
set "PATH=%WB_NODE_DIR%;%PATH%"
set "DSH=C:\Users\stk_gb\dsh-deploy"
set "FL=D:\codespace\05-开源项目\freellmapi"
set "PATH=%DSH%\node_modules\.bin;%PATH%"
cd /d "%DSH%"
REM 读取当前 freellmapi key 并注入环境变量 (recover 会重置 key，必须动态取)
for /f "delims=" %%k in ('"%PY%" "%FL%\get_key.py"') do set "FREELLMAPI_API_KEY=%%k"
echo [%time%] FREELLMAPI_API_KEY=%FREELLMAPI_API_KEY:~0,12%... >> "%FL%\dsh_web.log"
echo [%time%] dsh web starting ... >> "%FL%\dsh_web.log"
dsh web --no-open >> "%FL%\dsh_web.log" 2>&1
echo [%time%] dsh web exited (code %errorlevel%) >> "%FL%\dsh_web.log"
