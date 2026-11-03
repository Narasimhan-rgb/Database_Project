@echo off
cd /d "%~dp0"
echo ==========================================
echo ENGAGE V8 - STUDENT OPPORTUNITY INTELLIGENCE
echo PostgreSQL live app + optional Oracle mirror
echo ==========================================
echo.
echo Make sure PostgreSQL is running first.
echo Neo4j and MongoDB are NOT required.
echo.
if not exist .venv python -m venv .venv
call .venv\Scripts\activate
python -m pip install -r requirements.txt
if not exist .env copy .env.example .env

echo.
echo --- Creating PostgreSQL schema ---
python setup_postgres.py
if errorlevel 1 goto :fail

echo.
echo --- Loading ENGAGE V8 sample data ---
python seed.py
if errorlevel 1 goto :fail

echo.
echo --- Starting ENGAGE V8 ---
python app.py
goto :end

:fail
echo.
echo Setup failed. Check PostgreSQL service and .env credentials.
pause
exit /b 1

:end
pause
