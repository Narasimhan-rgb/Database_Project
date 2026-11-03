@echo off
setlocal
cd /d "%~dp0"
title ENGAGE V11 - Install demo data and start
if not exist ".env" (
 echo [ERROR] Missing .env file.
 echo Copy your old ENGAGE .env file here, or run:
 echo copy .env.example .env
 echo notepad .env
 pause
 exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
 echo [1/5] Creating a Python virtual environment...
 python -m venv .venv
 if errorlevel 1 goto :fail
)
call ".venv\Scripts\activate.bat"
echo [2/5] Installing Python packages...
python -m pip install -r requirements.txt
if errorlevel 1 goto :fail
echo [3/5] Creating/updating PostgreSQL schema (no data reset)...
python setup_postgres.py
if errorlevel 1 goto :fail
echo [4/5] Adding 25 students + 25 posts + 20 resources safely...
python demo_expansion.py
if errorlevel 1 goto :fail
echo [5/5] Starting ENGAGE: http://127.0.0.1:5000
python app.py
pause
exit /b 0
:fail
echo Installation failed. Check PostgreSQL is running and your .env credentials.
pause
exit /b 1
