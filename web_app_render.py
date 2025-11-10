#!/usr/bin/env python3
"""
Root-level web app entry point for Render deployment
Bypasses path issues by running directly from project root
"""
import sys
import os
import threading
import time
from datetime import datetime

# Ensure src is in Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Import after path setup
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
import redis
import json
import uuid

# Import services
from config import config
from services.file_service import FileService
from services.generator_service import GeneratorService, Question
from services.html_renderer import HTMLRenderer
from utils.logger import logger

# Global telegram updater for webhook processing
telegram_updater = None

def set_telegram_updater(updater):
    """Set the telegram updater for webhook processing"""
    global telegram_updater
    telegram_updater = updater

# Configure Flask app with templates at root level (copied by build.sh)
current_file_dir = os.path.dirname(os.path.abspath(__file__))
print(f"DEBUG: Root web app file location: {__file__}")
print(f"DEBUG: Current file dir: {current_file_dir}")
print(f"DEBUG: Working directory: {os.getcwd()}")

# Simple template detection for root-level deployment
template_dir = os.path.join(current_file_dir, 'templates')
static_dir = os.path.join(current_file_dir, 'static')

print(f"DEBUG: Template directory: {template_dir}")
print(f"DEBUG: Template directory exists: {os.path.exists(template_dir)}")
print(f"DEBUG: Static directory: {static_dir}")
print(f"DEBUG: Static directory exists: {os.path.exists(static_dir)}")

# Verify critical templates
if os.path.exists(template_dir):
    template_files = os.listdir(template_dir)
    print(f"DEBUG: Template files found: {template_files}")
else:
    print("WARNING: Templates directory not found - using fallback mode")
    template_dir = None

app = Flask(__name__,
           template_folder=template_dir,
           static_folder=static_dir)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'mcq-bot-secret-key-change-in-production')

# Configure file uploads
UPLOAD_FOLDER = os.path.join(config.TEMP_DIR, 'web_uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = config.MAX_FILE_SIZE_BYTES

# Initialize services
file_service = FileService()
generator_service = GeneratorService()
html_renderer = HTMLRenderer()

# Redis for session management
try:
    redis_client = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)
    redis_client.ping()
    logger.info("Connected to Redis for web sessions")
except Exception as e:
    logger.warning(f"Redis not available for web app: {e}")
    redis_client = None

def allowed_file(filename):
    """Check if file type is allowed"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ['pdf', 'docx', 'txt']

def get_session_key(session_id: str) -> str:
    """Get Redis key for session"""
    return f"web_session:{session_id}"

def save_session_data(session_id: str, data: dict) -> bool:
    """Save data to session"""
    if not redis_client:
        return False
    try:
        redis_client.setex(get_session_key(session_id), 3600, json.dumps(data))
        return True
    except Exception as e:
        logger.error(f"Failed to save session data: {e}")
        return False

def get_session_data(session_id: str) -> dict:
    """Get data from session"""
    if not redis_client:
        return None
    try:
        data = redis_client.get(get_session_key(session_id))
        return json.loads(data) if data else None
    except Exception as e:
        logger.error(f"Failed to get session data: {e}")
        return None

@app.route('/')
def index():
    """Home page"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Failed to render index.html: {e}")
        # Fallback HTML if template not found
        return '''
        <!DOCTYPE html>
        <html lang="he" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Telegram MCQ Bot</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; direction: rtl; background: #f5f5f5; }
                .container { max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .btn { display: inline-block; padding: 15px 30px; margin: 10px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; font-size: 18px; }
                .btn:hover { background: #0056b3; }
                .error { color: #e74c3c; margin: 20px 0; font-size: 14px; }
                h1 { color: #2c3e50; margin-bottom: 10px; }
                p { color: #7f8c8d; margin-bottom: 30px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 Telegram MCQ Bot</h1>
                <div class="error">⚠️ Template system running in fallback mode</div>
                <p>בוט ליצירת מבחני בחירה מרובה באמצעות AI</p>
                <a href="/upload" class="btn">🚀 התחל ליצור מבחן</a>
                <br>
                <a href="/debug-paths" class="btn" style="background: #6c757d;">🔧 מידע טכני</a>
            </div>
        </body>
        </html>
        ''', 200

@app.route('/upload', methods=['GET', 'POST'])
def upload_files():
    """File upload page"""
    if request.method == 'GET':
        try:
            return render_template('upload.html')
        except Exception as e:
            logger.error(f"Failed to render upload.html: {e}")
            # Fallback HTML
            return '''
            <!DOCTYPE html>
            <html lang="he" dir="rtl">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>העלאת קבצים - MCQ Bot</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 20px; direction: rtl; background: #f5f5f5; }
                    .container { max-width: 700px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
                    .upload-form { border: 3px dashed #ddd; padding: 40px; margin: 20px 0; text-align: center; border-radius: 10px; }
                    input[type="file"] { margin: 15px; padding: 10px; font-size: 16px; }
                    .btn { padding: 15px 30px; margin: 15px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 18px; }
                    .btn:hover { background: #218838; }
                    .back-btn { background: #6c757d; }
                    .back-btn:hover { background: #5a6268; }
                    .error { color: red; margin: 20px 0; }
                    h1 { color: #2c3e50; text-align: center; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>📁 העלאת קבצים</h1>
                    <div class="error">⚠️ Template system running in fallback mode</div>
                    <form method="post" enctype="multipart/form-data" class="upload-form">
                        <h3>בחר קבצים (PDF, DOCX, TXT)</h3>
                        <p>עד 15MB, מספר קבצים מותר</p>
                        <input type="file" name="files" multiple accept=".pdf,.docx,.txt" required>
                        <br>
                        <button type="submit" class="btn">📤 העלה קבצים</button>
                    </form>
                    <a href="/" class="btn back-btn">🏠 חזור לדף הבית</a>
                </div>
            </body>
            </html>
            ''', 200
    
    # Handle file upload logic (simplified for fallback)
    return jsonify({"status": "upload endpoint working", "fallback": True}), 200

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check template system
        template_status = os.path.exists(app.template_folder) if app.template_folder else False
        
        # Check Redis connection  
        redis_status = False
        try:
            if redis_client:
                redis_client.ping()
                redis_status = True
        except:
            pass
        
        # Check critical templates
        critical_templates = ['index.html', 'upload.html', 'questions.html', 'quiz.html']
        missing_templates = []
        if app.template_folder:
            for template in critical_templates:
                template_path = os.path.join(app.template_folder, template)
                if not os.path.exists(template_path):
                    missing_templates.append(template)
        else:
            missing_templates = critical_templates
        
        health_data = {
            'status': 'healthy' if not missing_templates else 'degraded',
            'service': 'telegram-mcq-bot-web',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'version': '1.0.0',
            'deployment_info': {
                'template_folder': app.template_folder,
                'template_system_working': template_status,
                'redis_connected': redis_status,
                'missing_templates': missing_templates,
                'fallback_mode': not template_status,
                'telegram_bot_enabled': config.RUN_TELEGRAM_BOT,
                'webhook_mode': config.USE_WEBHOOK,
                'gemini_model': config.GEMINI_MODEL,
                'working_directory': os.getcwd(),
                'script_location': __file__
            }
        }
        
        status_code = 200 if health_data['status'] == 'healthy' else 503
        return jsonify(health_data), status_code
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'service': 'telegram-mcq-bot-web',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'error': str(e)
        }), 500

@app.route('/debug-paths')
def debug_paths():
    """Debug endpoint to check file structure"""
    debug_info = {
        'working_dir': os.getcwd(),
        'script_location': __file__,
        'template_folder': app.template_folder,
        'static_folder': app.static_folder,
        'template_folder_exists': os.path.exists(app.template_folder) if app.template_folder else False,
        'static_folder_exists': os.path.exists(app.static_folder) if app.static_folder else False,
    }
    
    try:
        debug_info['root_dir_contents'] = os.listdir('.')
    except:
        debug_info['root_dir_contents'] = 'Error listing'
        
    try:
        if app.template_folder and os.path.exists(app.template_folder):
            debug_info['template_files'] = os.listdir(app.template_folder)
        else:
            debug_info['template_files'] = 'templates dir not found'
    except Exception as e:
        debug_info['template_files'] = f'Error: {e}'
    
    return f"<pre>{json.dumps(debug_info, indent=2)}</pre>"

@app.route(f'/{config.TELEGRAM_BOT_TOKEN}', methods=['POST'])
def webhook():
    """Handle Telegram webhook updates"""
    if not config.USE_WEBHOOK:
        return 'Webhook not enabled', 404
    
    try:
        if telegram_updater is None:
            logger.warning("Telegram updater not set")
            return 'Bot not ready', 503
            
        # Get the JSON data from request
        update_data = request.get_json(force=True)
        
        # Process the update using the telegram updater
        from telegram import Update
        update = Update.de_json(update_data, telegram_updater.bot)
        
        if update:
            telegram_updater.dispatcher.process_update(update)
        
        return 'OK', 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return 'Error', 500

def run_telegram_bot():
    """Run Telegram bot in background"""
    try:
        time.sleep(2)  # Let Flask start first
        print("Starting Telegram bot...")
        
        # Import and run bot
        import main as src_main
        updater = src_main.main(run_as_thread=True)
        
        if updater:
            print("Telegram bot initialized successfully")
            set_telegram_updater(updater)
            # Keep thread alive
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("Telegram bot stopping...")
                if hasattr(updater, 'stop'):
                    updater.stop()
        
    except Exception as e:
        print(f"Telegram bot error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # Check if we should run telegram bot
    run_telegram = os.environ.get('RUN_TELEGRAM_BOT', 'true').lower() == 'true'
    
    if run_telegram:
        print("Telegram bot will start in background...")
        # Start Telegram bot in background thread
        telegram_thread = threading.Thread(target=run_telegram_bot, daemon=True)
        telegram_thread.start()
    else:
        print("Telegram bot disabled")
    
    # Run Flask app
    port = int(os.environ.get('PORT', 10000))
    print(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)