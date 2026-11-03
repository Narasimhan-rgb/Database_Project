@echo off
cd /d "%~dp0"
if not exist .venv (
  echo Run FIRST_RUN_SETUP.bat first.
  pause
  exit /b 1
)
call .venv\Scripts\activate
python app.py
pause
