#!/usr/bin/env python3
"""
Telegram MCQ Bot - Web Service Entry Point
Entry point that runs both the Telegram bot and a Flask web interface
"""
import sys
import os
import threading
import time
from datetime import datetime

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Import modules
import main as src_main

def run_flask_app():
    """Run Flask web application"""
    try:
        # Import here to ensure src is in path
        from web_app import app
        
        port = int(os.environ.get('PORT', 10000))
        print(f"Starting Flask web app on port {port}")
        
        # Run Flask app
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            threaded=True
        )
    except Exception as e:
        print(f"Flask app error: {e}")

def run_telegram_bot():
    """Run Telegram bot"""
    try:
        # Small delay to let Flask start first
        time.sleep(2)
        print("Starting Telegram bot...")
        src_main.main()
    except Exception as e:
        print(f"Telegram bot error: {e}")

def main():
    """Main entry point that runs both Flask web app and Telegram bot"""
    try:
        print("Starting MCQ Bot hybrid service")
        
        # Check if we should run telegram bot (for local development)
        run_telegram = os.environ.get('RUN_TELEGRAM_BOT', 'true').lower() == 'true'
        
        if run_telegram:
            print("Telegram bot will start in 3 seconds...")
            # Start Telegram bot in background thread
            telegram_thread = threading.Thread(target=run_telegram_bot, daemon=True)
            telegram_thread.start()
        else:
            print("Telegram bot disabled (set RUN_TELEGRAM_BOT=true to enable)")
        
        print("Starting Flask web interface...")
        # Run Flask app in main thread (this will block)
        run_flask_app()
        
    except KeyboardInterrupt:
        print("Received stop signal, shutting down...")
    except Exception as e:
        print(f"Error starting hybrid service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()