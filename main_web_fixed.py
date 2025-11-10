#!/usr/bin/env python3
"""
Simplified entry point for Render deployment
Runs from root directory to avoid path issues
"""
import os
import sys
import threading
import time

# Add current directory to Python path (instead of src)
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'src'))

def run_flask_app():
    """Run Flask web application"""
    try:
        # Change to src directory for templates
        src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
        os.chdir(src_dir)
        print(f"Changed to src directory: {os.getcwd()}")
        
        # Now import and run
        sys.path.insert(0, os.getcwd())
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
        import traceback
        traceback.print_exc()

def run_telegram_bot():
    """Run Telegram bot"""
    try:
        # Small delay to let Flask start first
        time.sleep(2)
        print("Starting Telegram bot...")
        
        # Change to src directory
        src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
        os.chdir(src_dir)
        sys.path.insert(0, os.getcwd())
        
        import main as src_main
        updater = src_main.main(run_as_thread=True)
        
        # If we got an updater back, keep the thread alive
        if updater:
            print("Telegram bot initialized successfully")
            # Keep this thread alive to process background jobs
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("Telegram bot thread stopping...")
                if hasattr(updater, 'stop'):
                    updater.stop()
        
    except Exception as e:
        print(f"Telegram bot error: {e}")
        import traceback
        traceback.print_exc()

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