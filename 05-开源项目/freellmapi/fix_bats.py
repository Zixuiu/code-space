# -*- coding: utf-8 -*-
import os

FL = r"D:\codespace\05-开源项目\freellmapi"
DSH = r"C:\Users\stk_gb\dsh-deploy"
NODE = r"C:\Users\stk_gb\.workbuddy\binaries\node\versions\22.22.2"
PY = r"C:\Users\stk_gb\.workbuddy\binaries\python\versions\3.13.12\python.exe"

# ---------- 1) recover_freellmapi.bat : 去掉结尾的 pause（避免 call 同步调用时阻塞） ----------
recover = """@echo off
setlocal
set "WB_NODE_DIR={node}"
set "PATH=%WB_NODE_DIR%;%PATH%"
set "ROOT=%~dp0"
echo === recover_freellmapi.bat : 恢复免费 API 后端 ===
echo.
echo [1/5] 生成 server/.env (ENCRYPTION_KEY) ...
if exist "%ROOT%server\\.env" goto :have_env
powershell -NoProfile -Command "$k=([BitConverter]::ToString((1..32|%%{{Get-Random -Maximum 256}})) -replace '-',''); Set-Content -Path '%ROOT%server\\.env' -Value "ENCRYPTION_KEY=$k`nPORT=3001`nNODE_ENV=production" -Encoding utf8"
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
if exist "%ROOT%server\\data\\freeapi.db" del "%ROOT%server\\data\\freeapi.db"
echo.
echo [5/5] 启动服务 (后台隐藏运行) ...
taskkill /IM node.exe /F
timeout /t 2 /nobreak >nul
powershell -NoProfile -Command "Start-Process -FilePath '%WB_NODE_DIR%\\node.exe' -ArgumentList 'dist/index.js' -WorkingDirectory '%ROOT%server' -WindowStyle Hidden -RedirectStandardOutput '%ROOT%freellmapi_server.log' -RedirectStandardError '%ROOT%freellmapi_server.err'"
timeout /t 15 /nobreak >nul
cd /d "%ROOT%"
node bootstrap.mjs
echo.
echo === 完成。服务日志: %ROOT%freellmapi_server.log ===
echo === 上面的 Unified API Key 就是新的免费端点密钥 ===
""".format(node=NODE)
recover_path = os.path.join(FL, "recover_freellmapi.bat")
open(recover_path, "wb").write(recover.replace("\n", "\r\n").encode("gbk"))
print("recover written, pause removed:", "pause" not in recover)

# ---------- 2) get_key.py : 从后端日志动态提取当前 key ----------
getkey = """# -*- coding: utf-8 -*-
import re, os
log = r"{fl}\\freellmapi_server.log"
if os.path.exists(log):
    text = open(log, encoding="utf-8", errors="replace").read()
    m = list(re.finditer(r"unified API key\\s*:\\s*(freellmapi-[\\w]+)", text, re.IGNORECASE))
    if m:
        print(m[-1].group(1))
""".format(fl=FL)
getkey_path = os.path.join(FL, "get_key.py")
open(getkey_path, "w", encoding="utf-8").write(getkey)
print("get_key.py written")

# ---------- 3) start_dsh.bat : 启动前把当前 key 注入 FREELLMAPI_API_KEY ----------
start_dsh = """@echo off
set "WB_NODE_DIR={node}"
set "PY={py}"
set "PATH=%WB_NODE_DIR%;%PATH%"
set "DSH={dsh}"
set "FL={fl}"
set "PATH=%DSH%\\node_modules\\.bin;%PATH%"
cd /d "%DSH%"
REM 读取当前 freellmapi key 并注入环境变量 (recover 会重置 key，必须动态取)
for /f "delims=" %%k in ('"%PY%" "%FL%\\get_key.py"') do set "FREELLMAPI_API_KEY=%%k"
echo [%time%] FREELLMAPI_API_KEY=%FREELLMAPI_API_KEY:~0,12%... >> "%FL%\\dsh_web.log"
echo [%time%] dsh web starting ... >> "%FL%\\dsh_web.log"
dsh web --no-open >> "%FL%\\dsh_web.log" 2>&1
echo [%time%] dsh web exited (code %errorlevel%) >> "%FL%\\dsh_web.log"
""".format(node=NODE, py=PY, dsh=DSH, fl=FL)
start_dsh_path = os.path.join(FL, "start_dsh.bat")
open(start_dsh_path, "wb").write(start_dsh.replace("\n", "\r\n").encode("gbk"))
print("start_dsh.bat written with key injection")
