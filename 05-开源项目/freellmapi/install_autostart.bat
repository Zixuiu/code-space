@echo off
setlocal
set "ROOT=%~dp0"
echo === install_autostart.bat : register FreeLLMAPI as logon autostart (background, no window) ===
echo.
schtasks /create /tn "FreeLLMAPI" /tr "cmd /c %ROOT%freellmapi_svc.bat" /sc onlogon /rl highest /f
echo.
echo === done. FreeLLMAPI auto-starts hidden on Windows logon ===
echo === uninstall: schtasks /delete /tn "FreeLLMAPI" /f ===
pause
