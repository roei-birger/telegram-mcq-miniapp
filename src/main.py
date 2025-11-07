"""
Telegram MCQ Bot - Main Entry Point
בוט טלגרם ליצירת מבחני בחירה מרובה (MCQ) באמצעות AI
"""
import sys

# Python 3.13 compatibility patch - must be imported before telegram
try:
    import imghdr
except ModuleNotFoundError:
    from src import imghdr_compat  # Loads the compatibility module

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

from src.config import config
from src.utils.logger import logger, setup_logger
from src.services.queue_service import queue_service
from src.handlers.start import start
from src.handlers.document import handle_document
from src.handlers.text import handle_text
from src.handlers.callback import handle_callback_query
from src.handlers.health import health_check


def main():
    """Main function - אתחול והרצת הבוט"""
    
    try:
        # בדיקת configuration
        logger.info("Starting Telegram MCQ Bot...")
        config.validate()
        logger.info("Configuration validated")
        
        # יצירת תיקיות נדרשות
        config.ensure_directories()
        logger.info("Directories created")
        
        # Setup logging עם level מה-config
        setup_logger(log_level=config.LOG_LEVEL)
        
        # אתחול Updater
        logger.info("Initializing Telegram bot...")
        updater = Updater(token=config.TELEGRAM_BOT_TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        
        # רישום handlers
        logger.info("Registering handlers...")
        
        # Command handlers
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("health", health_check))
        
        # Message handlers
        dispatcher.add_handler(MessageHandler(Filters.document, handle_document))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
        
        # Callback query handler
        dispatcher.add_handler(CallbackQueryHandler(handle_callback_query))
        
        # הפעלת background workers
        logger.info("Starting background workers...")
        queue_service.start_workers(num_workers=3)
        
        # התחלת polling
        logger.info("🚀 Telegram MCQ Bot is running!")
        logger.info(f"Using Google Gemini ({config.GEMINI_MODEL})")
        logger.info("Press Ctrl+C to stop")
        
        updater.start_polling()
        updater.idle()
        
    except KeyboardInterrupt:
        logger.info("Received stop signal")
        queue_service.stop_workers()
        logger.info("Bot stopped")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
