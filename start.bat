@echo off
REM Quick start script for Windows

echo 🚀 Starting Telegram MCQ Bot...

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    py -3.11 -m venv venv
)

REM Activate virtual environment
echo ✨ Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt

REM Check .env file
if not exist ".env" (
    echo ⚠️ .env file not found!
    echo Please create .env file from .env.example
    pause
    exit /b 1
)

REM Start bot
echo 🤖 Starting bot...
set PYTHONPATH=%CD%
python main.py

pause
