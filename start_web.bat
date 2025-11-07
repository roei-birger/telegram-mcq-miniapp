@echo off
chcp 65001 >nul
REM Start both Flask web app and Telegram bot

echo Starting MCQ Bot Web Application + Telegram Bot...

REM Set Python path
set PYTHONPATH=%CD%\src

REM Enable both services
set RUN_TELEGRAM_BOT=true

REM Check .env file
if not exist ".env" (
    echo .env file not found!
    echo Please create .env file from .env.example
    pause
    exit /b 1
)

echo Starting Flask web interface...
echo Telegram bot will start automatically in 3 seconds...
echo.
echo Access the web interface at: http://localhost:10000
echo Press Ctrl+C to stop both services
echo.

REM Run the hybrid application
python main_web.py

pause