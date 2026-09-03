@echo off
cd /d "%~dp0"
python "%~dp0Ò»¼üÀ­È¡.py"
if errorlevel 1 (echo FAILED) else (echo DONE)
pause
