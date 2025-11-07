"""
Input validators
פונקציות לאימות קלט מהמשתמש
"""
from typing import Tuple
from src.config import config


def validate_file_size(file_size: int) -> Tuple[bool, str]:
    """
    בדיקת גודל קובץ
    
    Args:
        file_size: גודל הקובץ בבייטים
    
    Returns:
        (is_valid, error_message)
    """
    if file_size > config.MAX_FILE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        return False, f"⚠️ הקובץ גדול מדי ({size_mb:.1f}MB). מקסימום: {config.MAX_FILE_SIZE_MB}MB. נסה קובץ קטן יותר."
    
    return True, ""


def validate_file_type(mime_type: str) -> Tuple[bool, str]:
    """
    בדיקת סוג קובץ נתמך
    
    Args:
        mime_type: MIME type של הקובץ
    
    Returns:
        (is_valid, error_message)
    """
    if mime_type not in config.SUPPORTED_MIME_TYPES:
        supported = ", ".join(config.SUPPORTED_MIME_TYPES.values())
        return False, f"⚠️ סוג קובץ לא נתמך. סוגים נתמכים: {supported}"
    
    return True, ""


def validate_question_count(count_str: str) -> Tuple[bool, int, str]:
    """
    בדיקת מספר שאלות תקין
    
    Args:
        count_str: מספר השאלות כטקסט
    
    Returns:
        (is_valid, count, error_message)
    """
    try:
        count = int(count_str)
    except ValueError:
        return False, 0, f"⚠️ אנא שלח מספר תקין (בין {config.MIN_QUESTIONS} ל-{config.MAX_QUESTIONS})"
    
    if count < config.MIN_QUESTIONS:
        return False, count, f"⚠️ מינימום {config.MIN_QUESTIONS} שאלות"
    
    if count > config.MAX_QUESTIONS:
        return False, count, f"⚠️ מקסימום {config.MAX_QUESTIONS} שאלות"
    
    return True, count, ""


def validate_text_length(text: str, min_words: int = 50) -> Tuple[bool, str]:
    """
    בדיקה שיש מספיק טקסט ליצירת שאלות
    
    Args:
        text: הטקסט שחולץ
        min_words: מינימום מילים נדרש
    
    Returns:
        (is_valid, error_message)
    """
    word_count = len(text.split())
    
    if word_count < min_words:
        return False, f"⚠️ הטקסט קצר מדי ({word_count} מילים). נדרש לפחות {min_words} מילים ליצירת שאלות איכותיות."
    
    if not text.strip():
        return False, "⚠️ לא נמצא טקסט בקובץ"
    
    return True, ""
