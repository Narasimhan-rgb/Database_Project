@echo off
cd /d "%~dp0src"
if not exist .venv (
  echo First install: see README.md for setup, virtual environment and database creation.
  pause
  exit /b 1
)
call .venv\Scripts\activate
python app.py
pause
