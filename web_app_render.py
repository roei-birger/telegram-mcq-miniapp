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
from services.queue_service import QueueService
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

# Enhanced template detection for deployment
possible_template_paths = [
    # If we're in /opt/render/project/src, go up to project root
    os.path.join(os.path.dirname(current_file_dir), 'templates'),  # ../templates (from src to root)
    
    # Standard root-level paths
    os.path.join(current_file_dir, 'templates'),                   # ./templates (same level as script)
    
    # Working directory variations
    os.path.join(os.getcwd(), 'templates'),                       # cwd/templates
    os.path.join(os.getcwd(), '..', 'templates'),                 # cwd/../templates
    
    # Hardcoded Render paths
    '/opt/render/project/templates',                              # Direct Render path
]

template_dir = None
static_dir = None

print("=== ROOT APP TEMPLATE SEARCH ===")
for path in possible_template_paths:
    abs_path = os.path.abspath(path)
    exists = os.path.exists(abs_path)
    is_dir = os.path.isdir(abs_path) if exists else False
    print(f"  Checking: {abs_path} -> exists={exists}, is_dir={is_dir}")
    
    if exists and is_dir:
        # Check if index.html exists
        index_path = os.path.join(abs_path, 'index.html')
        has_index = os.path.exists(index_path)
        print(f"    Has index.html: {has_index}")
        
        if has_index:
            template_dir = abs_path
            print(f"  ✅ SELECTED TEMPLATE DIR: {template_dir}")
            
            # Find static directory relative to templates
            static_candidates = [
                os.path.join(os.path.dirname(abs_path), 'static'),  # Same level as templates
                os.path.join(current_file_dir, 'static'),           # Same level as script
                os.path.join(os.getcwd(), 'static'),               # cwd/static
            ]
            
            for static_path in static_candidates:
                if os.path.exists(static_path):
                    static_dir = static_path
                    print(f"  ✅ SELECTED STATIC DIR: {static_dir}")
                    break
            
            break

if not template_dir:
    print("⚠️  NO TEMPLATES FOUND - Using None (fallback mode)")
    template_dir = None

if not static_dir:
    # Fallback static directory
    static_dir = os.path.join(current_file_dir, 'static')
    print(f"  → DEFAULT STATIC: {static_dir}")

print(f"\n🎯 FINAL CONFIGURATION:")
print(f"  Template directory: {template_dir}")
print(f"  Static directory: {static_dir}")
print(f"  Template exists: {os.path.exists(template_dir) if template_dir else False}")
print(f"  Static exists: {os.path.exists(static_dir) if static_dir else False}")

# Verify critical templates if template_dir exists
if template_dir and os.path.exists(template_dir):
    template_files = os.listdir(template_dir)
    print(f"  📄 Template files found: {template_files}")
    
    critical_templates = ['index.html', 'upload.html', 'questions.html', 'quiz.html']
    missing = [t for t in critical_templates if not os.path.exists(os.path.join(template_dir, t))]
    if missing:
        print(f"  ⚠️  Missing templates: {missing}")
    else:
        print(f"  ✅ All critical templates found!")
else:
    print("  ⚠️  Templates directory not found - fallback mode will be used")

print("=" * 50)

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

# Initialize queue service
try:
    if redis_client:
        queue_service = QueueService()
        logger.info("Queue service initialized")
    else:
        queue_service = None
        logger.warning("Queue service not available - Redis required")
except Exception as e:
    logger.error(f"Failed to initialize queue service: {e}")
    queue_service = None

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
    
    # Handle file upload logic 
    if 'files' not in request.files:
        flash('לא נבחר קובץ', 'error')
        return redirect(request.url)
    
    files = request.files.getlist('files')
    if not files or all(f.filename == '' for f in files):
        flash('לא נבחר קובץ', 'error')
        return redirect(request.url)
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id
    
    processed_files = []
    total_words = 0
    
    for file in files:
        if file and file.filename != '' and allowed_file(file.filename):
            # Save file
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{filename}")
            file.save(file_path)
            
            try:
                # Process file - determine MIME type from extension
                ext = filename.lower().split('.')[-1]
                mime_type_map = {
                    'pdf': 'application/pdf',
                    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'txt': 'text/plain'
                }
                mime_type = mime_type_map.get(ext, 'text/plain')
                
                text_result = file_service.extract_text(file_path, mime_type)
                if text_result and text_result.get('text'):
                    text = text_result['text']
                    word_count = text_result.get('word_count', len(text.split()))
                    processed_files.append({
                        'filename': filename,
                        'path': file_path,
                        'text': text,
                        'word_count': word_count
                    })
                    total_words += word_count
                    print(f"Web: Processed {filename} - {word_count:,} words")
                else:
                    flash(f'לא ניתן לחלץ טקסט מקובץ {filename}', 'error')
                    os.remove(file_path)
            except Exception as e:
                logger.error(f"Error processing file {filename}: {e}")
                flash(f'שגיאה בעיבוד קובץ {filename}', 'error')
                if os.path.exists(file_path):
                    os.remove(file_path)
        else:
            flash(f'סוג קובץ לא נתמך: {file.filename}', 'error')
    
    if not processed_files:
        flash('לא נמצאו קבצים תקינים לעיבוד', 'error')
        return redirect(request.url)
    
    # Check if total text is too large
    if total_words > 50000:
        flash(f'הקובץ גדול מדי ({total_words:,} מילים). מקסימום: 50,000 מילים.', 'error')
        return redirect(request.url)
    
    # Save session data
    session_data = {
        'files': processed_files,
        'total_words': total_words,
        'timestamp': datetime.now().isoformat()
    }
    
    if not save_session_data(session_id, session_data):
        flash('שגיאה בשמירת נתונים. השרת עמוס, נסה שוב מאוחר יותר.', 'error')
        return redirect(url_for('index'))
    
    return redirect(url_for('select_questions'))

@app.route('/questions', methods=['GET', 'POST'])
def select_questions():
    """Question count selection page"""
    if request.method == 'GET':
        # Try to render template first
        try:
            session_id = session.get('session_id')
            if not session_id:
                flash('סשן פג תוקף, אנא התחל מחדש', 'error')
                return redirect(url_for('index'))
            
            # Get session data
            session_data = get_session_data(session_id)
            if not session_data or not session_data.get('files'):
                flash('לא נמצאו קבצים, אנא התחל מחדש', 'error')
                return redirect(url_for('index'))
            
            # Calculate recommended questions based on word count
            total_words = session_data['total_words']
            if total_words < 500:
                recommended = min(5, max(3, total_words // 100))
            elif total_words < 2000:
                recommended = min(15, max(5, total_words // 150))
            else:
                recommended = min(50, max(15, total_words // 200))
            
            return render_template('questions.html', 
                                 files=session_data['files'],
                                 total_words=total_words,
                                 recommended=recommended)
        except Exception as e:
            logger.error(f"Failed to render questions.html: {e}")
            return '''
            <!DOCTYPE html>
            <html lang="he" dir="rtl">
            <head>
                <meta charset="UTF-8">
                <title>בחירת שאלות - MCQ Bot</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 20px; direction: rtl; background: #f5f5f5; }
                    .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
                    .form-group { margin: 20px 0; }
                    input[type="number"] { padding: 10px; font-size: 16px; width: 100px; }
                    .btn { padding: 15px 30px; margin: 10px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
                    .btn:hover { background: #218838; }
                    .back-btn { background: #6c757d; }
                    .error { color: red; margin: 20px 0; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🎯 בחירת מספר שאלות</h1>
                    <div class="error">⚠️ Template system running in fallback mode</div>
                    <form method="post">
                        <div class="form-group">
                            <label>מספר שאלות רצוי (3-50):</label><br>
                            <input type="number" name="question_count" min="3" max="50" value="10" required>
                        </div>
                        <button type="submit" class="btn">🚀 צור מבחן</button>
                    </form>
                    <a href="/upload" class="btn back-btn">🔙 חזור לעלאת קבצים</a>
                </div>
            </body>
            </html>
            ''', 200

    # Handle POST request - question count selection
    try:
        question_count = int(request.form.get('question_count', 0))
        if not (3 <= question_count <= 50):  # config.MIN_QUESTIONS and MAX_QUESTIONS
            flash(f'מספר שאלות חייב להיות בין 3 ל-50', 'error')
            return redirect(request.url)
        
        # Update session data
        session_id = session.get('session_id')
        if session_id:
            session_data = get_session_data(session_id)
            if session_data:
                session_data['question_count'] = question_count
                save_session_data(session_id, session_data)
        
        return redirect(url_for('generate_quiz'))
        
    except ValueError:
        flash('מספר שאלות לא תקין', 'error')
        return redirect(request.url)

@app.route('/generate')  
def generate_quiz():
    """Background quiz generation route"""
    session_id = session.get('session_id')
    
    if not session_id:
        flash('סשן פג תוקף, אנא התחל מחדש', 'error')
        return redirect(url_for('index'))
    
    session_data = get_session_data(session_id)
    if not session_data or not session_data.get('files') or not session_data.get('question_count'):
        flash('מידע חסר, אנא התחל מחדש', 'error')
        return redirect(url_for('index'))
    
    # Add generation job to queue
    try:
        if not queue_service:
            flash('שירות התורים אינו זמין - Redis נדרש', 'error')
            return redirect(url_for('select_questions'))
            
        job_id = queue_service.add_job({
            'session_id': session_id,
            'type': 'generate_web',
            'files': session_data['files'],
            'question_count': session_data['question_count']
        })
        
        # Store job ID in session
        session_data['job_id'] = job_id
        session_data['job_status'] = 'queued'
        save_session_data(session_id, session_data)
        
    except Exception as e:
        logger.error(f"Failed to add job to queue: {e}")
        flash('שגיאה בהפעלת יצירת המבחן', 'error')
        return redirect(url_for('select_questions'))
    
    # Render status page with polling
    try:
        return render_template('quiz.html', session_id=session_id, job_id=job_id)
    except Exception as e:
        logger.error(f"Failed to render quiz.html: {e}")
        return f'''
        <!DOCTYPE html>
        <html lang="he" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>יצירת מבחן - MCQ Bot</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; direction: rtl; background: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; text-align: center; }}
                .spinner {{ border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 40px; height: 40px; animation: spin 2s linear infinite; margin: 20px auto; }}
                @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
                .status {{ margin: 20px 0; padding: 15px; background: #e3f2fd; border-radius: 5px; }}
                #status-message {{ font-size: 18px; margin: 20px; }}
                #result {{ margin: 20px; display: none; }}
                .btn {{ padding: 15px 30px; margin: 10px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; text-decoration: none; display: inline-block; }}
            </style>
            <script>
                let pollCount = 0;
                function checkStatus() {{
                    if (pollCount > 60) return; // Stop after 5 minutes
                    
                    fetch('/status/' + '{session_id}')
                        .then(response => response.json())
                        .then(data => {{
                            const statusEl = document.getElementById('status-message');
                            const resultEl = document.getElementById('result');
                            
                            if (data.status === 'completed' && data.questions) {{
                                statusEl.textContent = '✅ הושלם! המבחן מוכן';
                                resultEl.innerHTML = data.questions;
                                resultEl.style.display = 'block';
                                document.querySelector('.spinner').style.display = 'none';
                            }} else if (data.status === 'error') {{
                                statusEl.textContent = '❌ שגיאה: ' + data.error;
                                document.querySelector('.spinner').style.display = 'none';
                            }} else {{
                                statusEl.textContent = '⏳ מעבד... ' + (data.message || '');
                                pollCount++;
                                setTimeout(checkStatus, 5000);
                            }}
                        }})
                        .catch(err => {{
                            document.getElementById('status-message').textContent = '❌ שגיאת רשת';
                            document.querySelector('.spinner').style.display = 'none';
                        }});
                }}
                
                // Start polling when page loads
                window.onload = () => setTimeout(checkStatus, 2000);
            </script>
        </head>
        <body>
            <div class="container">
                <h1>🎯 יוצר מבחן</h1>
                <div class="spinner"></div>
                <div class="status">
                    <div id="status-message">⏳ מתחיל יצירת המבחן...</div>
                </div>
                <div id="result"></div>
                <a href="/upload" class="btn">🔄 צור מבחן חדש</a>
            </div>
        </body>
        </html>
        '''

@app.route('/quiz')
def show_quiz():
    """Quiz display page"""
    return jsonify({"status": "quiz endpoint working", "fallback": True}), 200

@app.route('/status/<session_id>')
def check_status(session_id):
    """Check generation status"""
    try:
        session_data = get_session_data(session_id)
        if not session_data:
            return jsonify({'status': 'error', 'error': 'Session not found'})
        
        job_id = session_data.get('job_id')
        if not job_id:
            return jsonify({'status': 'error', 'error': 'No job found'})
        
        # Get job status from queue service
        if not queue_service:
            return jsonify({'status': 'error', 'error': 'Queue service not available'})
            
        job_status = queue_service.get_job_status(job_id)
        
        if job_status == 'completed':
            # Get generated questions
            questions = session_data.get('generated_questions')
            if questions:
                html_content = html_renderer.render_questions_html(questions)
                return jsonify({'status': 'completed', 'questions': html_content})
        
        return jsonify({
            'status': job_status, 
            'message': session_data.get('status_message', '')
        })
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return jsonify({'status': 'error', 'error': str(e)})


@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({"error": f"File too large. Max size: {config.MAX_FILE_SIZE_MB}MB"}), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return '''
    <!DOCTYPE html>
    <html lang="he" dir="rtl">
    <head><meta charset="UTF-8"><title>שגיאה 404</title>
    <style>body{font-family:Arial;text-align:center;padding:50px;direction:rtl;}</style></head>
    <body><h1>שגיאה 404</h1><p>הדף לא נמצא</p><a href="/">חזור לדף הבית</a></body>
    </html>
    ''', 404

@app.errorhandler(500) 
def server_error(e):
    """Handle 500 errors"""
    logger.error(f"Server error: {e}")
    return '''
    <!DOCTYPE html>
    <html lang="he" dir="rtl">
    <head><meta charset="UTF-8"><title>שגיאה 500</title>
    <style>body{font-family:Arial;text-align:center;padding:50px;direction:rtl;}</style></head>
    <body><h1>שגיאה 500</h1><p>שגיאה פנימית בשרת</p><a href="/">חזור לדף הבית</a></body>
    </html>
    ''', 500

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