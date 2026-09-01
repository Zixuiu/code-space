@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PY=
where py >nul 2>nul && set PY=py -3
if not defined PY set PY=python
if not exist .venv (%PY% -m venv .venv)
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt -q
python run.py
pause
