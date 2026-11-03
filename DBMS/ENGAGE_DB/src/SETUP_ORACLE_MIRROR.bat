@echo off
cd /d "%~dp0"
call .venv\Scripts\activate

echo ==========================================
echo ENGAGE Oracle Mirror Setup + Safe Sync
echo ==========================================
echo.

python -m pip install oracledb
if errorlevel 1 goto :fail

echo.
echo --- Checking / creating Oracle schema ---
python setup_oracle.py
if errorlevel 1 goto :fail

echo.
echo --- Synchronizing PostgreSQL data to Oracle ---
python sync_postgres_to_oracle.py
if errorlevel 1 goto :fail

echo.
echo ==========================================
echo Oracle mirror sync completed successfully.
echo Start the app with: python app.py
echo ==========================================
pause
exit /b 0

:fail
echo.
echo Oracle setup/sync failed.
echo Check the detailed error shown above.
pause
exit /b 1
