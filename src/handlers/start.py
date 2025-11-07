"""
Start Handler
טיפול בפקודת /start
"""
from telegram import Update
from telegram.ext import CallbackContext

from src.services.session_service import session_service
from src.utils.logger import logger


def start(update: Update, context: CallbackContext) -> None:
    """
    Handler לפקודת /start
    
    Args:
        update: Telegram update
        context: Callback context
    """
    try:
        chat_id = update.effective_chat.id
        
        logger.info(f"User {chat_id} started bot")
        
        # בדיקת rate limiting
        is_allowed, error_msg = session_service.check_rate_limit(chat_id)
        if not is_allowed:
            update.message.reply_text(error_msg)
            return
        
        # יצירת session חדשה
        session_service.create_session(chat_id)
        session_service.increment_rate_limit(chat_id)
        
        # הודעת ברוכים הבאים
        welcome_message = """🤖 **ברוכים הבאים לבוט יצירת מבחני MCQ!**

אני יכול ליצור עבורך מבחן אמריקאי (שאלות בחירה מרובה) מכל חומר לימוד.

📋 **איך זה עובד?**
1. העלה קובץ PDF, DOCX או TXT (עד 20MB)
2. אגיד לך כמה מילים מצאתי ואמליץ על מספר שאלות
3. בחר כמה שאלות רוצה (3-50)
4. תוך דקה-שתיים תקבל קובץ HTML עם המבחן!

✨ **מה מיוחד?**
• יצירה אוטומטית עם Google Gemini AI
• התפלגות קושי חכמה (10% קל, 20% בינוני, 40% קשה, 30% קשה מאוד)
• HTML אינטראקטיבי עם תמיכה בעברית מלאה
• הסברים מפורטים לכל שאלה
• **תמיכה במספר קבצים** - העלה מספר קבצים ואני אאחד אותם למבחן אחד!

💡 **טיפ:** אם הקובץ שלך גדול מ-20MB, פצל אותו לחלקים והעלה את כולם!

🚀 **בוא נתחיל!**
העלה קובץ עכשיו 👇"""
        
        update.message.reply_text(
            welcome_message,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Start handler error: {e}")
        update.message.reply_text("❌ אירעה שגיאה. נסה שוב עם /start")
