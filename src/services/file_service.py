"""
File Service
עיבוד קבצים - חילוץ טקסט מ-PDF/DOCX/TXT
"""
import os
import chardet
from typing import Dict, Any, Optional
from PyPDF2 import PdfReader
from docx import Document

from utils.logger import logger


class FileService:
    """Service for processing uploaded files"""
    
    @staticmethod
    def extract_text(file_path: str, mime_type: str) -> Optional[Dict[str, Any]]:
        """
        חילוץ טקסט מקובץ
        
        Args:
            file_path: נתיב לקובץ
            mime_type: MIME type של הקובץ
        
        Returns:
            Dictionary עם text, word_count, char_count או None במקרה של שגיאה
        """
        try:
            if mime_type == "application/pdf":
                return FileService._extract_from_pdf(file_path)
            elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                return FileService._extract_from_docx(file_path)
            elif mime_type == "text/plain":
                return FileService._extract_from_txt(file_path)
            else:
                logger.error(f"Unsupported MIME type: {mime_type}")
                return None
        except Exception as e:
            logger.error(f"Failed to extract text: {e}")
            return None
    
    @staticmethod
    def _extract_from_pdf(file_path: str) -> Optional[Dict[str, Any]]:
        """
        חילוץ טקסט מ-PDF
        
        Args:
            file_path: נתיב לקובץ PDF
        
        Returns:
            Dictionary עם המידע או None
        """
        try:
            reader = PdfReader(file_path, strict=False)  # strict=False מאפשר קבצים פגומים
            
            # בדיקה אם הקובץ מוצפן
            if reader.is_encrypted:
                logger.warning("PDF file is encrypted")
                return {
                    "text": "",
                    "word_count": 0,
                    "char_count": 0,
                    "error": "הקובץ מוגן בסיסמה"
                }
            
            # חילוץ טקסט מכל הדפים
            text_parts = []
            for i, page in enumerate(reader.pages):
                try:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                except Exception as e:
                    logger.warning(f"Failed to extract page {i}: {e}")
                    continue
            
            full_text = "\n".join(text_parts).strip()
            
            if not full_text:
                return {
                    "text": "",
                    "word_count": 0,
                    "char_count": 0,
                    "error": "לא נמצא טקסט בקובץ PDF. אולי הקובץ מכיל רק תמונות או סרוק? נסה להמיר אותו לפורמט טקסט."
                }
            
            # סטטיסטיקות
            word_count = len(full_text.split())
            char_count = len(full_text)
            
            logger.info(f"Extracted {word_count} words from PDF ({len(reader.pages)} pages)")
            
            return {
                "text": full_text,
                "word_count": word_count,
                "char_count": char_count,
                "error": None
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"PDF extraction failed: {error_msg}")
            
            # הודעות שגיאה ידידותיות
            if "EOF marker not found" in error_msg or "EOF" in error_msg:
                friendly_msg = "הקובץ PDF פגום או לא הושלם. נסה:\n• להוריד מחדש את הקובץ\n• לפתוח ולשמור אותו מחדש ב-Adobe Reader\n• להמיר ל-DOCX או TXT"
            elif "encrypted" in error_msg.lower():
                friendly_msg = "הקובץ מוגן בסיסמה. הסר את ההגנה ונסה שוב."
            else:
                friendly_msg = f"שגיאה בקריאת PDF. נסה פורמט אחר (DOCX/TXT).\nשגיאה טכנית: {error_msg[:100]}"
            
            return {
                "text": "",
                "word_count": 0,
                "char_count": 0,
                "error": friendly_msg
            }
    
    @staticmethod
    def _extract_from_docx(file_path: str) -> Optional[Dict[str, Any]]:
        """
        חילוץ טקסט מ-DOCX
        
        Args:
            file_path: נתיב לקובץ DOCX
        
        Returns:
            Dictionary עם המידע או None
        """
        try:
            doc = Document(file_path)
            
            # חילוץ טקסט מכל הפסקאות
            text_parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text.strip())
            
            full_text = "\n".join(text_parts).strip()
            
            if not full_text:
                return {
                    "text": "",
                    "word_count": 0,
                    "char_count": 0,
                    "error": "לא נמצא טקסט בקובץ DOCX"
                }
            
            # סטטיסטיקות
            word_count = len(full_text.split())
            char_count = len(full_text)
            
            logger.info(f"Extracted {word_count} words from DOCX")
            
            return {
                "text": full_text,
                "word_count": word_count,
                "char_count": char_count,
                "error": None
            }
        except Exception as e:
            logger.error(f"DOCX extraction failed: {e}")
            return {
                "text": "",
                "word_count": 0,
                "char_count": 0,
                "error": f"שגיאה בקריאת DOCX: {str(e)}"
            }
    
    @staticmethod
    def _extract_from_txt(file_path: str) -> Optional[Dict[str, Any]]:
        """
        חילוץ טקסט מ-TXT
        
        Args:
            file_path: נתיב לקובץ TXT
        
        Returns:
            Dictionary עם המידע או None
        """
        try:
            # זיהוי encoding אוטומטי
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                detected = chardet.detect(raw_data)
                encoding = detected['encoding'] or 'utf-8'
            
            # קריאת הקובץ עם encoding מתאים
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    full_text = f.read().strip()
            except:
                # fallback ל-UTF-8 עם ignore
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    full_text = f.read().strip()
            
            if not full_text:
                return {
                    "text": "",
                    "word_count": 0,
                    "char_count": 0,
                    "error": "הקובץ ריק"
                }
            
            # סטטיסטיקות
            word_count = len(full_text.split())
            char_count = len(full_text)
            
            logger.info(f"Extracted {word_count} words from TXT (encoding: {encoding})")
            
            return {
                "text": full_text,
                "word_count": word_count,
                "char_count": char_count,
                "error": None
            }
        except Exception as e:
            logger.error(f"TXT extraction failed: {e}")
            return {
                "text": "",
                "word_count": 0,
                "char_count": 0,
                "error": f"שגיאה בקריאת TXT: {str(e)}"
            }
    
    @staticmethod
    def recommend_question_count(word_count: int) -> tuple[int, str]:
        """
        המלצה על מספר שאלות לפי אורך הטקסט
        
        Args:
            word_count: מספר מילים בטקסט
        
        Returns:
            (recommended_count, explanation)
        """
        if word_count < 200:
            return 5, "טקסט קצר"
        elif word_count < 500:
            return 8, "טקסט בינוני-קצר"
        elif word_count < 1000:
            return 15, "טקסט בינוני"
        elif word_count < 2000:
            return 25, "טקסט ארוך"
        else:
            return 35, "טקסט מקיף"


# Global instance
file_service = FileService()
