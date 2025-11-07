"""
Flask Web Application for MCQ Generation
ממשק אינטרנטי ליצירת מבחני בחירה מרובה
"""
import os
import uuid
from datetime import datetime
from typing import List, Optional
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
import redis
import json

# Import existing services
from config import config
from services.file_service import FileService
from services.generator_service import GeneratorService, Question
from services.html_renderer import HTMLRenderer
from utils.logger import logger

# Get absolute paths for templates and static files
current_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(current_dir, 'templates')
static_dir = os.path.join(current_dir, 'static')

# Configure Flask app template and static folders with absolute paths
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

def get_session_data(session_id: str) -> Optional[dict]:
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
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_files():
    """File upload page"""
    if request.method == 'GET':
        return render_template('upload.html')
    
    # Handle file upload
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
    
    # Save session data
    session_data = {
        'files': processed_files,
        'total_words': total_words,
        'timestamp': datetime.now().isoformat()
    }
    
    if not save_session_data(session_id, session_data):
        # Fallback to Flask session if Redis unavailable
        session['files'] = processed_files
        session['total_words'] = total_words
    
    return redirect(url_for('select_questions'))

@app.route('/questions', methods=['GET', 'POST'])
def select_questions():
    """Question count selection page"""
    session_id = session.get('session_id')
    if not session_id:
        flash('סשן פג תוקף, אנא התחל מחדש', 'error')
        return redirect(url_for('index'))
    
    # Get session data
    session_data = get_session_data(session_id) or {
        'files': session.get('files', []),
        'total_words': session.get('total_words', 0)
    }
    
    if not session_data.get('files'):
        flash('לא נמצאו קבצים, אנא התחל מחדש', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'GET':
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
    
    # Handle question count selection
    try:
        question_count = int(request.form.get('question_count', 0))
        if not (config.MIN_QUESTIONS <= question_count <= config.MAX_QUESTIONS):
            flash(f'מספר שאלות חייב להיות בין {config.MIN_QUESTIONS} ל-{config.MAX_QUESTIONS}', 'error')
            return redirect(request.url)
        
        # Update session data
        session_data['question_count'] = question_count
        if not save_session_data(session_id, session_data):
            session['question_count'] = question_count
        
        return redirect(url_for('generate_quiz'))
        
    except ValueError:
        flash('מספר שאלות לא תקין', 'error')
        return redirect(request.url)

@app.route('/generate')
def generate_quiz():
    """Generate quiz and show progress"""
    session_id = session.get('session_id')
    if not session_id:
        flash('סשן פג תוקף, אנא התחל מחדש', 'error')
        return redirect(url_for('index'))
    
    # Get session data
    session_data = get_session_data(session_id) or {
        'files': session.get('files', []),
        'question_count': session.get('question_count', 0)
    }
    
    files = session_data.get('files', [])
    question_count = session_data.get('question_count', 0)
    
    if not files or not question_count:
        flash('נתונים חסרים, אנא התחל מחדש', 'error')
        return redirect(url_for('index'))
    
    try:
        logger.info(f"Web: Generating {question_count} questions from {len(files)} files")
        
        # Generate questions
        if len(files) == 1:
            # Single file
            questions = generator_service._generate_questions_single(
                text=files[0]['text'],
                count=question_count,
                file_context=files[0]['filename']
            )
        else:
            # Multiple files
            questions = generator_service._generate_questions_multi_file(files, question_count)
        
        if not questions:
            flash('שגיאה ביצירת השאלות, אנא נסה שוב', 'error')
            return redirect(url_for('select_questions'))
        
        # Generate HTML
        metadata = {
            'filename': ', '.join([f['filename'] for f in files]),
            'total_words': sum(f.get('word_count', 0) for f in files),
            'question_count': len(questions)
        }
        html_content = html_renderer.render_quiz(questions, metadata)
        
        # Save quiz to session
        quiz_data = {
            'questions': [q.__dict__ for q in questions],
            'html': html_content,
            'generated_at': datetime.now().isoformat()
        }
        
        session_data['quiz'] = quiz_data
        if not save_session_data(session_id, session_data):
            session['quiz'] = quiz_data
        
        # Clean up uploaded files
        for file in files:
            if os.path.exists(file['path']):
                os.remove(file['path'])
        
        logger.info(f"Web: Successfully generated {len(questions)} questions")
        return redirect(url_for('show_quiz'))
        
    except Exception as e:
        logger.error(f"Error generating quiz: {e}")
        flash('שגיאה ביצירת המבחן, אנא נסה שוב', 'error')
        return redirect(url_for('select_questions'))

@app.route('/quiz')
def show_quiz():
    """Display the generated quiz"""
    session_id = session.get('session_id')
    if not session_id:
        flash('סשן פג תוקף, אנא התחל מחדש', 'error')
        return redirect(url_for('index'))
    
    # Get session data
    session_data = get_session_data(session_id) or {
        'quiz': session.get('quiz', {})
    }
    
    quiz_data = session_data.get('quiz', {})
    if not quiz_data:
        flash('לא נמצא מבחן, אנא צור מבחן חדש', 'error')
        return redirect(url_for('index'))
    
    return render_template('quiz.html', html_content=quiz_data['html'])

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'telegram-mcq-bot-web',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'version': '1.0.0'
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)