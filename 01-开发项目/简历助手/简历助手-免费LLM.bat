@echo off
cd /d "%~dp0"
rem ===== 1) 确保 FreeLLMAPI 网关在跑（已跑则跳过）=====
cd /d D:\codespace\05-开源项目\freellmapi
netstat -ano | findstr ":3001" >nul
if errorlevel 1 (
  if not exist node_modules (
    echo 首次运行，正在安装 FreeLLMAPI 依赖（约几分钟）...
    call npm install
  )
  echo 正在启动 FreeLLMAPI 网关...
  start "FreeLLMAPI" cmd /k "npm run dev"
  echo 等待网关就绪（约 40 秒）...
  timeout /t 40 >nul
) else (
  echo FreeLLMAPI 网关已在运行，跳过启动。
)
rem ===== 2) 切回简历助手目录并运行 =====
cd /d "%~dp0"
set PY=
where py >nul 2>nul && set PY=py -3
if not defined PY set PY=python
if not exist .venv (%PY% -m venv .venv)
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt -q
python run.py
pause
