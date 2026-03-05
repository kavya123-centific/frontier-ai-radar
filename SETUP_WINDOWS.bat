@echo off
echo.
echo ====================================================
echo  Frontier AI Radar - Windows Quick Setup
echo ====================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    echo Please install Python 3.10+ from https://python.org/downloads
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo [1/3] Python found. Installing dependencies...
pip install -r backend\requirements.txt
if errorlevel 1 (
    echo ERROR: pip install failed. Check your internet connection.
    pause
    exit /b 1
)

echo.
echo [2/3] Checking .env file...
if not exist backend\.env (
    echo Creating .env from template...
    copy backend\.env.example backend\.env
    echo.
    echo ACTION REQUIRED: Open backend\.env in Notepad and add your LLM_API_KEY
    echo Get a free key at: https://openrouter.ai
    echo.
    notepad backend\.env
    echo Press any key after saving your .env file...
    pause
)

echo.
echo [3/3] Starting Frontier AI Radar...
echo.
echo  Dashboard will open at: http://localhost:8501
echo  API Docs will open at:  http://localhost:8000/docs
echo  DB Explorer:            http://localhost:8000/admin/db
echo.
echo Press Ctrl+C to stop.
echo.
python start.py

pause
