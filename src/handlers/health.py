"""
Health Check Handler
בדיקת תקינות הבוט - למניעת cold starts
"""
from telegram import Update
from telegram.ext import CallbackContext
from datetime import datetime

from src.utils.logger import logger


def health_check(update: Update, context: CallbackContext) -> None:
    """
    Handler לפקודת /health
    מאפשר לשירותי monitoring לבדוק שהבוט רץ
    
    Args:
        update: Telegram update
        context: Callback context
    """
    try:
        logger.info(f"Health check from chat_id={update.effective_chat.id}")
        
        # תשובה קצרה
        update.message.reply_text(
            f"✅ Bot is healthy\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        update.message.reply_text("⚠️ Health check failed")
