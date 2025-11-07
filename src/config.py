"""
Configuration loader
טוען משתני סביבה ומספק config object גלובלי
"""
import os
from dotenv import load_dotenv

# טען משתני סביבה מקובץ .env
load_dotenv()


class Config:
    """Configuration class for the bot"""
    
    # Telegram Bot (חובה)
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # Google Gemini (חובה)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")
    
    # Redis
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    
    # הגדרות מערכת
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "15"))
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    MAX_QUESTIONS = int(os.getenv("MAX_QUESTIONS", "50"))
    MIN_QUESTIONS = 3
    
    # Rate Limiting
    RATE_LIMIT_PER_10MIN = int(os.getenv("RATE_LIMIT_PER_10MIN", "5"))
    RATE_LIMIT_PER_DAY = int(os.getenv("RATE_LIMIT_PER_DAY", "50"))
    
    # Session & Job TTLs (in seconds)
    SESSION_TTL = 900  # 15 minutes
    FILE_DATA_TTL = 259200  # 72 hours
    JOB_TIMEOUT = 600  # 10 minutes
    
    # Directories
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    TEMP_DIR = os.path.join(BASE_DIR, "temp")
    OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
    LOGS_DIR = os.path.join(BASE_DIR, "logs")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Supported file types
    SUPPORTED_MIME_TYPES = {
        "application/pdf": "PDF",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCX",
        "text/plain": "TXT"
    }
    
    @classmethod
    def validate(cls):
        """
        בדיקת תקינות של משתני סביבה חובה
        מעלה ValueError אם משהו חסר
        """
        errors = []
        
        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is required")
        
        if not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is required")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True
    
    @classmethod
    def ensure_directories(cls):
        """יצירת תיקיות נדרשות אם לא קיימות"""
        for directory in [cls.TEMP_DIR, cls.OUTPUTS_DIR, cls.LOGS_DIR]:
            os.makedirs(directory, exist_ok=True)


# Instance גלובלי
config = Config()
