@echo off
cd /d "%~dp0"
echo Checking Oracle sync patch...
findstr /N /C:"Parent tables come before child tables" sync_postgres_to_oracle.py
if errorlevel 1 (
    echo.
    echo PATCH NOT INSTALLED.
    echo Make sure these files are in the ENGAGE project folder.
    pause
    exit /b 1
)
echo.
echo PATCH INSTALLED CORRECTLY.
echo Now run SETUP_ORACLE_MIRROR.bat
pause
