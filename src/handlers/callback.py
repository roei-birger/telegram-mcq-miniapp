"""
Callback Query Handler
טיפול בלחיצות על כפתורים inline
"""
import time
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from config import config
from services.session_service import session_service
from services.queue_service import queue_service
from services.file_service import file_service
from utils.validators import validate_question_count
from utils.logger import logger


def handle_callback_query(update: Update, context: CallbackContext) -> None:
    """
    Handler ללחיצות על כפתורים inline
    
    Args:
        update: Telegram update
        context: Callback context
    """
    try:
        query = update.callback_query
        query.answer()  # מאשר את הלחיצה
        
        chat_id = query.message.chat_id
        callback_data = query.data
        
        logger.info(f"User {chat_id} clicked button: {callback_data}")
        
        # טיפול מיוחד לכפתורי העלאת קבצים
        if callback_data == "add_more_files":
            # שמירת state כ-AWAITING_COUNT כדי שהקובץ הבא יתווסף לרשימה הקיימת
            session_service.update_session_state(chat_id, "AWAITING_COUNT")
            query.edit_message_text(
                text="📤 **הוסף קובץ נוסף**\n\nהעלה את הקובץ הבא, והוא יתווסף לקבצים הקיימים.\n\n✨ כל הטקסט יאוחד יחד כשתיצור את המבחן!\n\n💡 אחרי שתעלה את הקובץ תוכל להחליט:\n• להוסיף עוד קבצים\n• להמשיך ליצירת המבחן",
                parse_mode='Markdown'
            )
            logger.info(f"User {chat_id} chose to add more files - keeping existing files")
            return
        
        if callback_data.startswith("rmfile_"):
            # הסרת קובץ ספציפי לפי אינדקס
            try:
                file_index = int(callback_data.replace("rmfile_", ""))
            except ValueError:
                query.edit_message_text("❌ שגיאה בפענוח הכפתור.")
                return
            
            file_data = session_service.get_file_data(chat_id)
            
            if not file_data or "files" not in file_data:
                query.edit_message_text("❌ שגיאה בהסרת הקובץ. התחל מחדש.")
                return
            
            files_list = file_data["files"]
            
            # בדיקה שהאינדקס תקין
            if file_index < 0 or file_index >= len(files_list):
                query.edit_message_text("❌ קובץ לא נמצא.")
                return
            
            # שמירת שם הקובץ שנמחק
            removed_filename = files_list[file_index]["filename"]
            
            # הסרת הקובץ מהרשימה
            files_list.pop(file_index)
            
            if len(files_list) == 0:
                # אם הסרנו את הקובץ האחרון
                session_service.delete_file_data(chat_id)
                query.edit_message_text(
                    text="✅ הקובץ הוסר.\n\n📤 העלה קובץ חדש כדי להתחיל.",
                    parse_mode='Markdown'
                )
                session_service.update_session_state(chat_id, "AWAITING_DOCUMENT")
                return
            
            # חישוב מחדש של הסטטיסטיקות
            total_word_count = sum(f["word_count"] for f in files_list)
            total_char_count = sum(f["char_count"] for f in files_list)
            combined_text = "\n\n".join(f["text"] for f in files_list)
            
            # עדכון file_data
            file_data = {
                "file_id": files_list[0]["file_id"],
                "filename": " + ".join([f["filename"] for f in files_list]),
                "mime_type": files_list[0]["mime_type"],
                "file_size": sum(f["file_size"] for f in files_list),
                "text": combined_text,
                "word_count": total_word_count,
                "char_count": total_char_count,
                "files": files_list,
                "num_files": len(files_list)
            }
            session_service.save_file_data(chat_id, file_data)
            
            # המלצה מחדש
            recommended, reason = file_service.recommend_question_count(total_word_count)
            
            # יצירת כפתורים - כמו במקורי
            keyboard = []
            
            # כפתור הסרה לכל קובץ (רק אם יש יותר מקובץ אחד)
            if len(files_list) > 1:
                for i, f in enumerate(files_list):
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
            
            # הודעה מעודכנת
            files_info = "\n".join([f"  {i+1}. {f['filename']} ({f['word_count']:,} מילים)" for i, f in enumerate(files_list)])
            
            remove_hint = "\n\n🗑️ **להסרת קובץ:** לחץ על הקובץ שברצונך להסיר מהרשימה למעלה" if len(files_list) > 1 else ""
            
            response = f"""✅ **הקובץ "{removed_filename}" הוסר בהצלחה!**

📁 **קבצים נותרו ({len(files_list)}):**
{files_info}

📊 **סטטיסטיקות מצטברות:**
• מילים: {total_word_count:,}
• תווים: {total_char_count:,}

💡 **המלצה:** {recommended} שאלות ({reason}){remove_hint}"""
            
            query.edit_message_text(
                text=response,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        if callback_data == "proceed_to_quiz":
            # המשך לשאלה כמה שאלות רוצים
            file_data = session_service.get_file_data(chat_id)
            if not file_data:
                query.edit_message_text("❌ הקובץ כבר לא זמין. בבקשה התחל מחדש עם /start")
                return
            
            query.edit_message_text(
                text=f"""📝 **כמה שאלות תרצה ליצור?**

📊 סה\"כ מילים: {file_data['word_count']:,}
💡 המלצה: {file_service.recommend_question_count(file_data['word_count'])[0]} שאלות

שלח מספר בין {config.MIN_QUESTIONS} ל-{config.MAX_QUESTIONS}""",
                parse_mode='Markdown'
            )
            session_service.update_session_state(chat_id, "AWAITING_COUNT")
            return
        
        # בדיקת session
        session = session_service.get_session(chat_id)
        if not session:
            query.message.reply_text(
                text="⚠️ ה-session פג. בבקשה התחל מחדש עם /start"
            )
            return
        
        # טיפול מיוחד למבחן חדש - לא צריך file_data
        if callback_data == "start_new_quiz":
            # משתמש רוצה להתחיל מבחן חדש - הצגת אישור
            keyboard = [
                [
                    InlineKeyboardButton("✅ כן, התחל מבחן חדש", callback_data="confirm_new_quiz"),
                    InlineKeyboardButton("❌ ביטול", callback_data="cancel_new_quiz")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # נשלח הודעה חדשה במקום לערוך (כי ההודעה המקורית היא document)
            query.message.reply_text(
                text="🔄 **התחל מבחן חדש?**\n\n⚠️ פעולה זו תמחק את כל הקבצים הקיימים מהזיכרון ותתחיל מחדש.\n\nהאם אתה בטוח?",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            return
        
        elif callback_data == "confirm_new_quiz":
            # אישור - מחיקת כל הקבצים והתחלה מחדש
            session_service.delete_file_data(chat_id)
            session_service.update_session_state(chat_id, "AWAITING_DOCUMENT")
            query.message.reply_text(
                text="✅ **מתחיל מבחן חדש**\n\n🗑️ כל הקבצים הקודמים נמחקו מהזיכרון\n\n📤 העלה קובץ PDF, DOCX או TXT (עד 20MB) כדי להתחיל",
                parse_mode='Markdown'
            )
            logger.info(f"User {chat_id} confirmed new quiz - cleared all files")
            return
        
        elif callback_data == "cancel_new_quiz":
            # ביטול - חזרה למסך הקודם
            query.message.reply_text(
                text="❌ **פעולה בוטלה**\n\nאתה יכול להמשיך ליצור מבחנים נוספים מהקבצים הקיימים.\n\nהעלה קובץ או שלח /start להתחלה מחדש.",
                parse_mode='Markdown'
            )
            return
        
        # בדיקה אם יש file data - נדרש לכל שאר הפעולות
        file_data = session_service.get_file_data(chat_id)
        if not file_data:
            query.message.reply_text(
                text="❌ הקובץ כבר לא זמין. בבקשה העלה קובץ חדש עם /start"
            )
            return
        
        if callback_data == "more_quiz_custom":
            # משתמש רוצה לבחור כמות מותאמת אישית
            session_service.update_session_state(chat_id, "AWAITING_COUNT")
            word_count = file_data.get("word_count", 0)
            query.message.reply_text(
                text=f"✏️ **כמה שאלות תרצה?**\n\n📊 הקובץ מכיל {word_count:,} מילים\n\n📝 שלח מספר בין {config.MIN_QUESTIONS} ל-{config.MAX_QUESTIONS}",
                parse_mode='Markdown'
            )
            return
        
        elif callback_data.startswith("more_quiz_"):
            # משתמש בחר כמות מוגדרת מראש
            try:
                count = int(callback_data.split("_")[2])
            except:
                query.message.reply_text(
                    text="❌ שגיאה בפענוח הכפתור"
                )
                return
            
            # Validation
            if count < config.MIN_QUESTIONS or count > config.MAX_QUESTIONS:
                query.message.reply_text(
                    text=f"❌ מספר שאלות לא תקין. צריך להיות בין {config.MIN_QUESTIONS} ל-{config.MAX_QUESTIONS}"
                )
                return
            
            # הודעת עיבוד
            processing_msg = query.message.reply_text(
                f"🚀 **מעבד את הבקשה...**\n\nיוצר {count} שאלות חדשות מהטקסט.\nזה יכול לקחת 10-60 שניות ⏱️",
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
            max_attempts = 120  # 10 דקות
            attempt = 0
            
            while attempt < max_attempts:
                time.sleep(5)
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
                        # שליחת קובץ HTML החדש
                        keyboard = [
                            [
                                InlineKeyboardButton("🔄 עוד מבחן (5)", callback_data=f"more_quiz_5"),
                                InlineKeyboardButton("🔄 עוד מבחן (10)", callback_data=f"more_quiz_10")
                            ],
                            [
                                InlineKeyboardButton("🔄 עוד מבחן (15)", callback_data=f"more_quiz_15"),
                                InlineKeyboardButton("🔄 עוד מבחן (20)", callback_data=f"more_quiz_20")
                            ],
                            [
                                InlineKeyboardButton("✏️ בחר כמות אחרת", callback_data=f"more_quiz_custom")
                            ],
                            [
                                InlineKeyboardButton("🔄 התחל מבחן חדש", callback_data=f"start_new_quiz")
                            ]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        with open(output_file, 'rb') as f:
                            query.message.reply_document(
                                document=f,
                                filename=os.path.basename(output_file),
                                caption=f"✅ **מבחן נוסף מוכן!**\n\n📝 {count} שאלות\n🎯 פתח את הקובץ בדפדפן\n\n💡 רוצה עוד?",
                                reply_markup=reply_markup
                            )
                        # מחיקת קובץ זמני
                        try:
                            os.remove(output_file)
                        except:
                            pass
                        processing_msg.delete()
                    else:
                        processing_msg.edit_text("❌ קובץ הפלט לא נמצא")
                    # עדכון state
                    session_service.update_session_state(chat_id, "COMPLETED")
                    return
                
                elif status == "FAILED":
                    # כשל
                    error = job_status.get("error", "שגיאה לא ידועה")
                    processing_msg.edit_text(
                        f"❌ **לא הצלחתי ליצור את המבחן**\n\n{error}\n\nנסה:\n• כמות שאלות אחרת\n• /start מחדש"
                    )
                    session_service.update_session_state(chat_id, "FAILED")
                    return
                
                # עדיין מעבד
                elif status == "PROCESSING" and attempt % 6 == 0:
                    dots = "." * ((attempt // 6) % 4)
                    processing_msg.edit_text(
                        f"⏳ **עדיין מעבד{dots}**\n\nיוצר שאלות עם AI. סבלנות 🙏"
                    )
            
            # Timeout
            processing_msg.edit_text(
                "⏱️ **הזמן הקצוב פג**\n\nהעיבוד ארך זמן רב. נסה שוב עם פחות שאלות."
            )
            session_service.update_session_state(chat_id, "FAILED")
            return
    
    except Exception as e:
        import traceback
        logger.error(f"Callback query handler error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        try:
            query.message.reply_text("❌ אירעה שגיאה. נסה שוב עם /start")
        except:
            pass
