# Copilot Instructions - Telegram MCQ Bot

## Project Overview

This is a **dual-interface MCQ generation system** that creates Hebrew multiple-choice quizzes from uploaded documents using Google Gemini AI. It operates as both a **Telegram bot** and a **Flask web application** that can run independently or together.

## Architecture & Core Components

### Entry Points & Deployment Strategy
- `main.py` - Root entry point for Telegram-only deployment
- `main_web.py` - **Hybrid entry point** running both Flask web app + Telegram bot
- `src/main.py` - Core bot logic with webhook/polling modes
- `src/web_app.py` - Flask application with file upload workflow
- All entry points handle **Python path injection** (`sys.path.insert(0, 'src')`)

### Service Layer Pattern
All business logic lives in `src/services/` as singleton instances:
- `generator_service.py` - **Gemini AI integration** with rate limiting & JSON parsing resilience
- `file_service.py` - PDF/DOCX/TXT text extraction
- `html_renderer.py` - Quiz HTML generation with RTL Hebrew support
- `queue_service.py` - **Redis-based background job processing** with 3 workers
- `session_service.py` - User session management for Telegram interactions

### Configuration & Environment
- `src/config.py` exports global `config` object
- **Deployment flexibility**: `USE_WEBHOOK`, `RUN_TELEGRAM_BOT`, `WEBHOOK_URL` env vars
- **Gemini model selection**: Default `gemini-pro`, recommended `gemini-2.0-flash`
- **Multi-environment**: Local (polling), Production (webhook), Web-only modes

## Critical Development Patterns

### Python 3.13 Compatibility Layer
```python
# Always import before telegram modules in main.py
try:
    import imghdr
except (ModuleNotFoundError, ImportError):
    import imghdr_compat  # Custom replacement module
```

### Telegram Bot Handler Structure
```python
# All handlers in src/handlers/ follow this pattern:
def handle_document(update, context):
    # 1. Extract chat_id and user validation
    # 2. Store file data in Redis sessions 
    # 3. Add job to background queue
    # 4. Send immediate acknowledgment
```

### Web Application Session Management
```python
# Redis-first sessions with Flask fallback
session_id = str(uuid.uuid4())
save_session_data(session_id, data)  # Redis with 3600s TTL
# NO Flask session for large data - reject if Redis unavailable
```

### Error-Resilient Gemini Integration
```python
# 3-retry logic with exponential backoff for rate limits
# JSON parsing with incomplete response recovery
# Text truncation to 40K chars for context limits
# Validation requiring 80% of requested questions minimum
```

## Development Workflows

### Local Development Commands
```bash
# Web + Bot hybrid (recommended)
bash start_web.sh  # or start_web.bat on Windows

# Environment setup
export PYTHONPATH="$(pwd)/src"  # Critical for imports
cp .env.example .env  # Fill TELEGRAM_BOT_TOKEN, GEMINI_API_KEY

# Redis requirement check
redis-cli ping  # Must return "PONG"
```

### Testing & Debugging
- **Web UI**: http://localhost:10000 for testing file upload flow
- **Debug endpoints**: `/debug-filesystem`, `/debug-paths` for deployment issues
- **Health check**: `/health` endpoint for monitoring
- **Telegram webhook**: `/{TELEGRAM_BOT_TOKEN}` POST endpoint

### File Processing Limitations
- **File size**: 15MB max (configurable via `MAX_FILE_SIZE_MB`)
- **Text limits**: 50K words max to prevent Gemini context overflow
- **Supported formats**: PDF, DOCX, TXT only
- **Question range**: 3-50 questions per document set

## Deployment Considerations

### Render.com Production Setup
- **Service type**: `web` (not worker) - requires HTTP endpoints
- **Build command**: `bash build.sh` (installs dependencies, sets permissions, **copies templates to root**)
- **Start command**: `python main_web.py` (hybrid web+bot)
- **Redis service**: Auto-configured via `render.yaml` environment injection
- **Template strategy**: `build.sh` copies `src/templates/` → `/templates/` for deployment compatibility

### Environment Variables for Production
```yaml
# render.yaml pattern
RUN_TELEGRAM_BOT: "true"    # Enable bot alongside web
USE_WEBHOOK: "true"         # Required for production Telegram
WEBHOOK_URL: "https://your-app.onrender.com"
GEMINI_MODEL: "gemini-2.0-flash"  # Faster than gemini-pro
FLASK_SECRET_KEY: "random-64-char-string"  # Security for sessions
```

### Health Check & Monitoring
- **Health endpoint**: `/health` returns deployment status, template verification, Redis connectivity
- **Debug endpoints**: `/debug-filesystem`, `/debug-paths` for deployment troubleshooting
- **Webhook endpoint**: `/{TELEGRAM_BOT_TOKEN}` for Telegram webhook processing

## Common Issues & Solutions

### Template Loading in Production
```python
# Enhanced robust path detection in web_app.py
possible_template_paths = [
    '/opt/render/project/templates',                    # Root templates in Render
    '/opt/render/project/src/templates',                # Src templates in Render  
    os.path.join(os.path.dirname(current_file_dir), 'templates'),  # ../templates from src
    os.path.join(os.getcwd(), 'templates'),             # cwd/templates
    # ... with index.html existence verification
]
# Always includes fallback HTML for critical routes when templates fail
```

### Bot Conflict Prevention
- **Issue**: Multiple `getUpdates` instances cause conflicts
- **Solution**: Use `drop_pending_updates=True` and proper cleanup
- **Web-only mode**: Set `RUN_TELEGRAM_BOT=false` to disable bot

### Template Not Found Errors
- **Issue**: `jinja2.exceptions.TemplateNotFound: index.html` in production
- **Root Cause**: Flask template path detection fails in deployment environments
- **Solution**: Enhanced path detection with multiple fallbacks and template existence verification
- **Fallback**: Critical routes (`/`, `/upload`) include inline HTML fallbacks when templates unavailable

### Rate Limiting Strategy
- **Gemini**: 2-second minimum intervals, exponential backoff for 429 errors
- **User limits**: 5 requests/10min, 50/day via Redis counters
- **Background processing**: 3 workers prevent API saturation

## Testing Integration Points

### Multi-file Question Generation
```python
# Proportional question allocation by word count
generator_service._generate_questions_multi_file(files, total_count)
# Tests should verify proportional distribution and shuffling
```

### Session Persistence
```python
# Telegram: Redis sessions with 15min TTL
# Web: Redis sessions with 1hr TTL, UUID-based
# Test session expiry and cleanup behavior
```

When working on this codebase, always consider the **dual-interface nature** - changes to services affect both Telegram and web workflows. Test both interfaces when modifying core business logic.