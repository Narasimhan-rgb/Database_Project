@echo off
cd /d "%~dp0"
if exist .venv\Scripts\python.exe (
  .venv\Scripts\python.exe demo_expansion.py
) else (
  python demo_expansion.py
)
pause
