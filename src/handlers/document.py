"""
Document Handler
טיפול בהעלאת קבצים
"""
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from config import config
from services.session_service import session_service
from services.file_service import file_service
from utils.validators import validate_file_size, validate_file_type, validate_text_length
from utils.logger import logger


def handle_document(update: Update, context: CallbackContext) -> None:
    """
    Handler להעלאת מסמכים
    
    Args:
        update: Telegram update
        context: Callback context
    """
    try:
        chat_id = update.effective_chat.id
        document = update.message.document
        
        logger.info(f"User {chat_id} uploaded file: {document.file_name}")
        logger.info(f"File size: {document.file_size} bytes ({document.file_size/(1024*1024):.2f}MB)")
        logger.info(f"Max allowed: {config.MAX_FILE_SIZE_BYTES} bytes ({config.MAX_FILE_SIZE_MB}MB)")
        
        # בדיקת session
        session = session_service.get_session(chat_id)
        if not session:
            update.message.reply_text("⚠️ בבקשה התחל עם /start")
            return
        
        # Validation: גודל קובץ
        is_valid, error_msg = validate_file_size(document.file_size)
        logger.info(f"File size validation result: {is_valid}, message: {error_msg}")
        if not is_valid:
            update.message.reply_text(error_msg)
            return
        
        # Validation: סוג קובץ
        mime_type = document.mime_type
        is_valid, error_msg = validate_file_type(mime_type)
        if not is_valid:
            update.message.reply_text(error_msg)
            return
        
        # הודעת עיבוד
        processing_msg = update.message.reply_text("⏳ מוריד ומעבד את הקובץ...")
        
        try:
            # הורדת הקובץ
            file = document.get_file()
            file_path = os.path.join(config.TEMP_DIR, f"{chat_id}_{document.file_name}")
            file.download(file_path)
            
            # חילוץ טקסט
            extraction_result = file_service.extract_text(file_path, mime_type)
            
            # מחיקת קובץ זמני
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # בדיקת תוצאה
            if not extraction_result or extraction_result.get("error"):
                error = extraction_result.get("error", "שגיאה לא ידועה") if extraction_result else "שגיאה בחילוץ טקסט"
                processing_msg.edit_text(f"❌ {error}")
                return
            
            text = extraction_result["text"]
            word_count = extraction_result["word_count"]
            
            # Validation: מספיק טקסט?
            is_valid, error_msg = validate_text_length(text)
            if not is_valid:
                processing_msg.edit_text(error_msg)
                return
            
            # בדיקה אם יש כבר קבצים שהועלו (מצב מיזוג)
            # אם ה-state הוא AWAITING_DOCUMENT זה אומר שהמשתמש התחיל מבחן חדש ורוצה להתחיל מחדש
            # אם ה-state הוא AWAITING_COUNT זה אומר שהמשתמש מוסיף קובץ נוסף לקבצים קיימים
            existing_file_data = session_service.get_file_data(chat_id)
            
            if session["state"] == "AWAITING_DOCUMENT":
                # מצב של מבחן חדש - נקה את הכל והתחל מחדש
                files_list = []
                logger.info(f"User {chat_id} starting fresh with new file (state=AWAITING_DOCUMENT)")
            elif session["state"] == "AWAITING_COUNT" and existing_file_data and "files" in existing_file_data:
                # מצב של הוספת קובץ נוסף לקבצים קיימים (לחץ "הוסף קובץ נוסף")
                files_list = existing_file_data.get("files", [])
                logger.info(f"User {chat_id} adding file to existing {len(files_list)} files (merging mode)")
            else:
                # אין קבצים קיימים או state לא מוכר
                files_list = []
                logger.info(f"User {chat_id} starting with empty files list")
            
            # הוספת הקובץ הנוכחי לרשימה
            files_list.append({
                "file_id": document.file_id,
                "filename": document.file_name,
                "mime_type": mime_type,
                "file_size": document.file_size,
                "text": text,
                "word_count": word_count,
                "char_count": extraction_result["char_count"]
            })
            
            # חישוב סטטיסטיקות מצטברות
            total_word_count = sum(f["word_count"] for f in files_list)
            total_char_count = sum(f["char_count"] for f in files_list)
            combined_text = "\n\n".join(f["text"] for f in files_list)
            
            # המלצה על מספר שאלות
            recommended, reason = file_service.recommend_question_count(total_word_count)
            
            # שמירת file data עם רשימת קבצים
            file_data = {
                "file_id": document.file_id,
                "filename": " + ".join([f["filename"] for f in files_list]),
                "mime_type": mime_type,
                "file_size": sum(f["file_size"] for f in files_list),
                "text": combined_text,
                "word_count": total_word_count,
                "char_count": total_char_count,
                "files": files_list,
                "num_files": len(files_list)
            }
            session_service.save_file_data(chat_id, file_data)
            
            # עדכון state
            session_service.update_session_state(chat_id, "AWAITING_COUNT")
            
            # יצירת כפתורי אופציות
            keyboard = []
            
            # כפתור הסרה לכל קובץ (רק אם יש יותר מקובץ אחד)
            if len(files_list) > 1:
                for i, f in enumerate(files_list):
                    # קיצור שם הקובץ אם הוא ארוך
                    short_name = f['filename'][:30] + "..." if len(f['filename']) > 30 else f['filename']
                    # שימוש באינדקס - callback_data מוגבל ל-64 בתים!
                    keyboard.append([
                        InlineKeyboardButton(
                            f"🗑️ {short_name} ({f['word_count']:,} מילים)",
                            callback_data=f"rmfile_{i}"
                        )
                    ])
            
            # כפתורי פעולה
            keyboard.append([InlineKeyboardButton("➕ הוסף קובץ נוסף", callback_data="add_more_files")])
            keyboard.append([InlineKeyboardButton("✅ המשך ליצירת מבחן", callback_data="proceed_to_quiz")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # הודעה למשתמש
            files_info = "\n".join([f"  {i+1}. {f['filename']} ({f['word_count']:,} מילים)" for i, f in enumerate(files_list)])
            
            remove_hint = "\n\n🗑️ **להסרת קובץ:** לחץ על הקובץ שברצונך להסיר מהרשימה למעלה" if len(files_list) > 1 else ""
            
            merge_hint = "\n\n✨ **שים לב:** כל הקבצים יאוחדו למבחן אחד!" if len(files_list) > 1 else ""
            
            response = f"""✅ **{'קובץ נוסף התווסף בהצלחה!' if len(files_list) > 1 else 'הקובץ עובד בהצלחה!'}**

📁 **קבצים ({len(files_list)}):**
{files_info}

📊 **סטטיסטיקות מצטברות:**
• מילים: {total_word_count:,}
• תווים: {total_char_count:,}

💡 **המלצה:** {recommended} שאלות ({reason}){merge_hint}{remove_hint}

❓ **רוצה להוסיף עוד קבצים או להמשיך ליצירת המבחן?**"""
            
            processing_msg.edit_text(response, parse_mode='Markdown', reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"File processing error: {e}")
            processing_msg.edit_text("❌ אירעה שגיאה בעיבוד הקובץ. נסה קובץ אחר.")
    
    except Exception as e:
        logger.error(f"Document handler error: {e}")
        update.message.reply_text("❌ אירעה שגיאה. נסה שוב עם /start")
