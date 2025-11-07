"""
Flask Web Application for MCQ Generation - Root Level Entry Point
ממשק אינטרנטי ליצירת מבחני בחירה מרובה
Fixed for Render deployment
"""
import os
import sys
import uuid
from datetime import datetime
from typing import List, Optional
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
import redis
import json

# Add src to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Import existing services
from config import config
from services.file_service import FileService
from services.generator_service import GeneratorService, Question
from services.html_renderer import HTMLRenderer
from utils.logger import logger

# Get absolute paths for templates and static files - FROM SRC DIRECTORY
template_dir = os.path.join(src_dir, 'templates')
static_dir = os.path.join(src_dir, 'static')

# Try multiple possible paths for templates
possible_template_paths = [
    template_dir,  # src/templates (expected)
    os.path.join(current_dir, 'templates'),  # ./templates
    os.path.join(current_dir, 'src', 'templates'),  # ./src/templates  
    'templates'  # relative fallback
]

template_path_found = None
for path in possible_template_paths:
    abs_path = os.path.abspath(path)
    if os.path.exists(abs_path) and os.path.isdir(abs_path):
        template_path_found = abs_path
        print(f"DEBUG: Found templates at: {template_path_found}")
        break

if not template_path_found:
    print("ERROR: No template directory found!")
    template_path_found = template_dir  # fallback

print(f"DEBUG: Current dir: {current_dir}")
print(f"DEBUG: SRC dir: {src_dir}")
print(f"DEBUG: Template dir: {template_path_found}")
print(f"DEBUG: Static dir: {static_dir}")
print(f"DEBUG: Templates exist: {os.path.exists(template_path_found)}")
if os.path.exists(template_path_found):
    print(f"DEBUG: Template files: {os.listdir(template_path_found)}")

# Configure Flask app template and static folders with absolute paths
app = Flask(__name__,
           template_folder=template_path_found,
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

def get_session_data(session_id):
    """Get session data from Redis"""
    if not redis_client:
        return None
    try:
        data = redis_client.get(f"web_session:{session_id}")
        return json.loads(data) if data else None
    except Exception as e:
        logger.error(f"Error getting session data: {e}")
        return None

def set_session_data(session_id, data):
    """Store session data in Redis"""
    if not redis_client:
        return False
    try:
        redis_client.setex(f"web_session:{session_id}", config.SESSION_TTL, json.dumps(data))
        return True
    except Exception as e:
        logger.error(f"Error setting session data: {e}")
        return False

def clear_session_data(session_id):
    """Clear session data from Redis"""
    if not redis_client:
        return False
    try:
        redis_client.delete(f"web_session:{session_id}")
        return True
    except Exception as e:
        logger.error(f"Error clearing session data: {e}")
        return False

@app.route('/')
def index():
    """Homepage with overview and quick start"""
    return render_template('index.html')

@app.route('/upload')
def upload_files():
    """File upload page"""
    return render_template('upload.html', 
                         max_file_size=config.MAX_FILE_SIZE_MB,
                         max_questions=config.MAX_QUESTIONS)

@app.route('/upload', methods=['POST'])
def handle_upload():
    """Handle file upload and processing"""
    try:
        # Check if files were uploaded
        if 'files' not in request.files:
            flash('לא נבחרו קבצים', 'error')
            return redirect(request.url)
        
        files = request.files.getlist('files')
        
        if not files or files[0].filename == '':
            flash('לא נבחרו קבצים', 'error')
            return redirect(request.url)
        
        # Validate and save files
        uploaded_files = []
        total_size = 0
        
        for file in files:
            if file.filename == '':
                continue
                
            if not allowed_file(file.filename):
                flash(f'סוג קובץ לא נתמך: {file.filename}. רק PDF, DOCX, TXT מותרים', 'error')
                return redirect(request.url)
            
            # Check file size (additional check)
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            total_size += file_size
            if total_size > config.MAX_FILE_SIZE_BYTES:
                flash(f'גודל הקבצים חורג מהמותר ({config.MAX_FILE_SIZE_MB}MB)', 'error')
                return redirect(request.url)
            
            # Save file
            filename = secure_filename(file.filename)
            filename = f"{uuid.uuid4()}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            uploaded_files.append(filepath)
        
        if not uploaded_files:
            flash('לא הועלו קבצים תקינים', 'error')
            return redirect(request.url)
        
        # Process files and extract text
        all_text = ""
        for filepath in uploaded_files:
            try:
                extracted_text = file_service.extract_text(filepath)
                if extracted_text:
                    all_text += extracted_text + "\n\n"
                # Clean up file
                os.remove(filepath)
            except Exception as e:
                logger.error(f"Error processing file {filepath}: {e}")
                if os.path.exists(filepath):
                    os.remove(filepath)
                flash(f'שגיאה בעיבוד קובץ: {os.path.basename(filepath)}', 'error')
                return redirect(request.url)
        
        if not all_text.strip():
            flash('לא הצלחנו לחלץ טקסט מהקבצים', 'error')
            return redirect(request.url)
        
        # Calculate suggested number of questions
        word_count = len(all_text.split())
        suggested_questions = min(max(word_count // 100, 5), config.MAX_QUESTIONS)
        
        # Store in session
        session_id = str(uuid.uuid4())
        session_data = {
            'text': all_text,
            'word_count': word_count,
            'suggested_questions': suggested_questions,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if set_session_data(session_id, session_data):
            return redirect(url_for('select_questions', session_id=session_id))
        else:
            flash('שגיאה בשמירת נתונים. אנא נסה שוב.', 'error')
            return redirect(request.url)
            
    except Exception as e:
        logger.error(f"Upload error: {e}")
        flash('אירעה שגיאה בהעלאת הקבצים', 'error')
        return redirect(request.url)

@app.route('/questions/<session_id>')
def select_questions(session_id):
    """Question count selection page"""
    session_data = get_session_data(session_id)
    
    if not session_data:
        flash('Session לא נמצא או פג תוקפו', 'error')
        return redirect(url_for('upload_files'))
    
    return render_template('questions.html',
                         session_id=session_id,
                         word_count=session_data['word_count'],
                         suggested_questions=session_data['suggested_questions'],
                         min_questions=config.MIN_QUESTIONS,
                         max_questions=config.MAX_QUESTIONS)

@app.route('/generate', methods=['POST'])
def generate_quiz():
    """Generate quiz with specified number of questions"""
    try:
        session_id = request.form.get('session_id')
        num_questions = int(request.form.get('num_questions', 10))
        
        # Validate input
        if not session_id:
            flash('Session ID חסר', 'error')
            return redirect(url_for('upload_files'))
        
        if not (config.MIN_QUESTIONS <= num_questions <= config.MAX_QUESTIONS):
            flash(f'מספר שאלות חייב להיות בין {config.MIN_QUESTIONS} ל-{config.MAX_QUESTIONS}', 'error')
            return redirect(url_for('select_questions', session_id=session_id))
        
        session_data = get_session_data(session_id)
        if not session_data:
            flash('Session לא נמצא או פג תוקפו', 'error')
            return redirect(url_for('upload_files'))
        
        # Generate questions using AI
        text = session_data['text']
        
        try:
            questions = generator_service.generate_questions(text, num_questions)
            
            if not questions:
                flash('לא הצלחנו ליצור שאלות מהטקסט', 'error')
                return redirect(url_for('select_questions', session_id=session_id))
            
            # Generate HTML quiz
            html_content = html_renderer.render_quiz(questions, f"מבחן - {num_questions} שאלות")
            
            # Clean up session
            clear_session_data(session_id)
            
            return render_template('quiz.html',
                                 html_content=html_content,
                                 num_questions=len(questions))
                                 
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            flash('שגיאה ביצירת השאלות. אנא נסה שוב.', 'error')
            return redirect(url_for('select_questions', session_id=session_id))
            
    except Exception as e:
        logger.error(f"Generate quiz error: {e}")
        flash('אירעה שגיאה ביצירת המבחן', 'error')
        return redirect(url_for('upload_files'))

@app.route('/download/<session_id>')
def download_quiz(session_id):
    """Download quiz as HTML file"""
    # This would be implemented if we stored the generated quiz
    flash('הורדת קובץ עדיין לא זמינה', 'info')
    return redirect(url_for('index'))

@app.route('/debug-paths')
def debug_paths():
    """Debug endpoint to check file structure in deployment"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    debug_info = {
        'current_working_dir': os.getcwd(),
        'script_location': __file__,
        'current_dir': current_dir,
        'src_dir': src_dir,
        'template_folder': app.template_folder,
        'static_folder': app.static_folder,
        'template_exists': os.path.exists(app.template_folder),
        'static_exists': os.path.exists(app.static_folder),
    }
    
    # List files in various directories
    try:
        debug_info['cwd_contents'] = os.listdir(os.getcwd())
    except:
        debug_info['cwd_contents'] = 'Error listing'
        
    try:
        debug_info['current_dir_contents'] = os.listdir(current_dir)
    except:
        debug_info['current_dir_contents'] = 'Error listing'
        
    try:
        debug_info['src_dir_contents'] = os.listdir(src_dir)
    except:
        debug_info['src_dir_contents'] = 'Error listing'
        
    try:
        if os.path.exists(app.template_folder):
            debug_info['template_files'] = os.listdir(app.template_folder)
        else:
            debug_info['template_files'] = 'Directory not found'
    except:
        debug_info['template_files'] = 'Error listing'
    
    return f"<pre>{json.dumps(debug_info, indent=2)}</pre>"

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'service': 'telegram-mcq-bot-web',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'version': '1.0.0',
        'template_folder': app.template_folder,
        'templates_exist': os.path.exists(app.template_folder)
    })

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    flash(f'קובץ גדול מדי. גודל מקסימלי: {config.MAX_FILE_SIZE_MB}MB', 'error')
    return redirect(url_for('upload_files'))

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return render_template('error.html', 
                         error_code=404,
                         error_message='הדף לא נמצא'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    logger.error(f"Server error: {e}")
    return render_template('error.html',
                         error_code=500,
                         error_message='שגיאה פנימית בשרת'), 500

@app.route(f'/{config.TELEGRAM_BOT_TOKEN}', methods=['POST'])
def webhook():
    """Handle Telegram webhook updates"""
    if not config.USE_WEBHOOK:
        return 'Webhook not enabled', 404
    
    try:
        # This endpoint is for webhook mode only
        # The actual telegram bot instance should handle this
        return 'Webhook endpoint - handled by bot instance', 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return 'Error', 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)