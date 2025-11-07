"""
Text Handler
טיפול בהודעות טקסט (מספר שאלות)
"""
import time
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from config import config
from services.session_service import session_service
from services.queue_service import queue_service
from utils.validators import validate_question_count
from utils.logger import logger


def handle_text(update: Update, context: CallbackContext) -> None:
    """
    Handler להודעות טקסט (מספר שאלות)
    
    Args:
        update: Telegram update
        context: Callback context
    """
    try:
        chat_id = update.effective_chat.id
        text = update.message.text.strip()
        
        logger.info(f"User {chat_id} sent text: {text}")
        
        # בדיקת session
        session = session_service.get_session(chat_id)
        if not session:
            update.message.reply_text("⚠️ בבקשה התחל עם /start")
            return
        
        # בדיקת state
        if session["state"] != "AWAITING_COUNT":
            update.message.reply_text("⚠️ בבקשה העלה קובץ תחילה")
            return
        
        # Validation: מספר שאלות
        is_valid, count, error_msg = validate_question_count(text)
        if not is_valid:
            update.message.reply_text(error_msg)
            return
        
        # קבלת file data
        file_data = session_service.get_file_data(chat_id)
        if not file_data:
            update.message.reply_text("❌ לא נמצא קובץ. בבקשה העלה קובץ שוב.")
            session_service.update_session_state(chat_id, "START")
            return
        
        # הודעת התחלה
        processing_msg = update.message.reply_text(
            f"🚀 **מעבד את הבקשה...**\n\nיוצר {count} שאלות מהטקסט.\nזה יכול לקחת 10-60 שניות ⏱️",
            parse_mode='Markdown'
        )
        
        # הוספה לתור
        metadata = {
            "filename": file_data.get("filename", "מבחן"),
            "word_count": file_data.get("word_count", 0)
        }
        
        # העברת file_info אם יש מספר קבצים
        file_info = None
        if "files" in file_data and len(file_data["files"]) > 1:
            file_info = {"files": file_data["files"]}
            logger.info(f"Passing {len(file_data['files'])} files info for proportional question distribution")
        
        job_id = queue_service.add_job(
            chat_id=chat_id,
            text=file_data["text"],
            question_count=count,
            metadata=metadata,
            file_info=file_info
        )
        
        if not job_id:
            processing_msg.edit_text("❌ אירעה שגיאה. נסה שוב.")
            return
        
        # עדכון state
        session_service.update_session_state(chat_id, "PROCESSING")
        
        # Polling על סטטוס
        max_attempts = 120  # 10 דקות (120 * 5 שניות)
        attempt = 0
        
        while attempt < max_attempts:
            time.sleep(5)  # המתנה 5 שניות
            attempt += 1
            
            job_status = queue_service.get_job_status(job_id)
            
            if not job_status:
                processing_msg.edit_text("❌ Job לא נמצא")
                return
            
            status = job_status["status"]
            
            if status == "COMPLETED":
                # הצלחה!
                output_file = job_status.get("output_file")
                if output_file and os.path.exists(output_file):
                    # יצירת כפתורים למבחן נוסף
                    keyboard = [
                        [
                            InlineKeyboardButton("🔄 מבחן נוסף (5 שאלות)", callback_data=f"more_quiz_5"),
                            InlineKeyboardButton("🔄 מבחן נוסף (10 שאלות)", callback_data=f"more_quiz_10")
                        ],
                        [
                            InlineKeyboardButton("🔄 מבחן נוסף (15 שאלות)", callback_data=f"more_quiz_15"),
                            InlineKeyboardButton("🔄 מבחן נוסף (20 שאלות)", callback_data=f"more_quiz_20")
                        ],
                        [
                            InlineKeyboardButton("✏️ בחר כמות אחרת", callback_data=f"more_quiz_custom")
                        ],
                        [
                            InlineKeyboardButton("� התחל מבחן חדש", callback_data=f"start_new_quiz")
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    # שליחת קובץ HTML
                    with open(output_file, 'rb') as f:
                        update.message.reply_document(
                            document=f,
                            filename=os.path.basename(output_file),
                            caption=f"✅ **המבחן מוכן!**\n\n📝 {count} שאלות\n🎯 פתח את הקובץ בדפדפן\n\n💡 רוצה מבחן נוסף מאותו הקובץ?",
                            reply_markup=reply_markup
                        )
                    
                    # מחיקת קובץ זמני
                    try:
                        os.remove(output_file)
                    except:
                        pass
                    
                    processing_msg.delete()
                    
                    # עדכון state אבל לא למחוק file_data!
                    session_service.update_session_state(chat_id, "COMPLETED")
                else:
                    processing_msg.edit_text("❌ קובץ הפלט לא נמצא")
                
                return
            
            elif status == "FAILED":
                # כשל
                error = job_status.get("error", "שגיאה לא ידועה")
                processing_msg.edit_text(
                    f"❌ **לא הצלחתי ליצור את המבחן**\n\n{error}\n\nנסה:\n• טקסט ארוך יותר\n• פחות שאלות\n• /start מחדש"
                )
                session_service.update_session_state(chat_id, "FAILED")
                return
            
            # עדיין מעבד
            elif status == "PROCESSING" and attempt % 6 == 0:  # כל 30 שניות
                dots = "." * ((attempt // 6) % 4)
                processing_msg.edit_text(
                    f"⏳ **עדיין מעבד{dots}**\n\nיוצר שאלות עם AI. סבלנות 🙏"
                )
        
        # Timeout
        processing_msg.edit_text(
            "⏱️ **הזמן הקצוב פג**\n\nהעיבוד ארך זמן רב.\n\nנסה:\n• קובץ קטן יותר\n• פחות שאלות\n• /start מחדש"
        )
        session_service.update_session_state(chat_id, "FAILED")
        
    except Exception as e:
        logger.error(f"Text handler error: {e}")
        update.message.reply_text("❌ אירעה שגיאה. נסה שוב עם /start")
