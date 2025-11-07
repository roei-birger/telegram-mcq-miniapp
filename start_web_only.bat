@echo off
chcp 65001 >nul
REM Start only Flask web app (without Telegram bot)

echo Starting MCQ Bot Web Interface Only...

REM Set Python path
set PYTHONPATH=%CD%\src

REM Disable Telegram bot
set RUN_TELEGRAM_BOT=false

REM Check .env file
if not exist ".env" (
    echo .env file not found!
    echo Please create .env file from .env.example
    pause
    exit /b 1
)

echo Starting Flask web interface...
echo.
echo Access the web interface at: http://localhost:10000
echo Press Ctrl+C to stop
echo.

REM Run only the Flask application
python main_web.py

pause