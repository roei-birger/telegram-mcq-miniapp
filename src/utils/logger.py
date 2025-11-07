"""
Logger utilities
הגדרת logging למערכת
"""
import logging
import os
from datetime import datetime


def setup_logger(name: str = "telegram_bot", log_level: str = "INFO") -> logging.Logger:
    """
    יצירת logger עם formatting מתאים
    
    Args:
        name: שם ה-logger
        log_level: רמת logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Logger object
    """
    # יצירת logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # מניעת duplicate handlers
    if logger.handlers:
        return logger
    
    # Format
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (אופציונלי - רק אם תיקיית logs קיימת)
    try:
        from src.config import config
        log_file = os.path.join(
            config.LOGS_DIR, 
            f"bot_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception:
        pass  # אם נכשל, נשתמש רק ב-console
    
    return logger


# Global logger instance
logger = setup_logger()
