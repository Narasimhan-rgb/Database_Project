@echo off
setlocal
cd /d "%~dp0"
echo --------------------------------------------
echo ENGAGE - Live Course Demand and Trends
 echo --------------------------------------------
if not exist ".env" (
  echo Missing .env - copy your original ENGAGE .env to this folder,
  echo or copy .env.example to .env and configure PostgreSQL credentials.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Setting up Python environment...
  python -m venv .venv
  if errorlevel 1 goto :fail
)
call ".venv\Scripts\activate.bat"
python -m pip install -r requirements.txt
if errorlevel 1 goto :fail
echo.
echo Installing additive PostgreSQL schema migration (no reseed)...
python setup_postgres.py
if errorlevel 1 goto :fail
echo.
echo Starting ENGAGE. Open http://127.0.0.1:5000 then Studio.
python app.py
pause
exit /b 0
:fail
echo.
echo Failed. Check PostgreSQL, Python or .env settings.
pause
exit /b 1
