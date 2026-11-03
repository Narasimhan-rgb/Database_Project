@echo off
cd /d "%~dp0"
call .venv\Scripts\activate
python -m query_lab.setup
python app.py
