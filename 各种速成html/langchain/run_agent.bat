@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ===================================================
echo  LangChain Real Agent - install deps then run
echo  (first run needs internet to pip install)
echo ===================================================
echo.
echo [1/2] Installing requirements...
py -3 -m pip install -r requirements.txt
if errorlevel 1 (
    echo  py launcher not found, trying "python"...
    python -m pip install -r requirements.txt
)

echo.
echo [2/2] Starting LangChain customer-service Agent...
echo  Type a message to chat. Type "exit" or "quit" to leave.
echo  Watch the "Entering new AgentExecutor chain" output = real Agent thinking.
echo.
py -3 langchain_app.py
if errorlevel 1 python langchain_app.py

pause
