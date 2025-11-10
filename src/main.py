"""
Telegram MCQ Bot - Main Entry Point
בוט טלגרם ליצירת מבחני בחירה מרובה (MCQ) באמצעות AI
"""
import sys
import os

# Python 3.13 compatibility patch - must be imported before telegram
try:
    import imghdr
except (ModuleNotFoundError, ImportError):
    try:
        import imghdr_compat  # Loads the compatibility module
    except ImportError:
        # If we can't import the compat module, create a minimal replacement
        class ImghdrModule:
            @staticmethod
            def what(file, h=None):
                return None
        sys.modules['imghdr'] = ImghdrModule()

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

# Import modules (paths should be set up by entry point)
from config import config
from utils.logger import logger, setup_logger
from services.queue_service import queue_service
from handlers.start import start
from handlers.document import handle_document
from handlers.text import handle_text
from handlers.callback import handle_callback_query
from handlers.health import health_check


def main(run_as_thread=False):
    """Main function - אתחול והרצת הבוט"""
    
    # Global updater for cleanup
    updater = None
    
    try:
        # בדיקת configuration
        logger.info("Starting Telegram MCQ Bot...")
        config.validate()
        logger.info("Configuration validated")
        
        # Check if we should run the bot
        if not config.RUN_TELEGRAM_BOT:
            logger.info("Telegram bot is disabled (RUN_TELEGRAM_BOT=false)")
            return
        
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
        
        # Choose between webhook and polling based on environment
        if config.USE_WEBHOOK and config.WEBHOOK_URL:
            logger.info(f"🚀 Starting Telegram Bot with webhook: {config.WEBHOOK_URL}")
            logger.info(f"Using Google Gemini ({config.GEMINI_MODEL})")
            logger.info("Webhook will be handled by Flask web app")
            
            # Set webhook URL
            updater.bot.set_webhook(
                url=f"{config.WEBHOOK_URL}/{config.TELEGRAM_BOT_TOKEN}",
                max_connections=100,
                allowed_updates=['message', 'callback_query']
            )
            
            logger.info("Webhook URL set successfully")
            
            # Set the updater in web_app for webhook processing
            try:
                from web_app import set_telegram_updater
                set_telegram_updater(updater)
                logger.info("Telegram updater set in web app")
            except ImportError:
                logger.warning("Could not import web_app to set updater")
            
            # Return the updater so main_web.py can manage it
            return updater
            
        else:
            # התחלת polling
            logger.info("🚀 Telegram MCQ Bot is running with polling!")
            logger.info(f"Using Google Gemini ({config.GEMINI_MODEL})")
            
            updater.start_polling(drop_pending_updates=True)
            
            if not run_as_thread:
                logger.info("Press Ctrl+C to stop")
                updater.idle()
            else:
                logger.info("Bot running as thread, no idle()")
                return updater
        
    except KeyboardInterrupt:
        logger.info("Received stop signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        # Cleanup
        try:
            if updater:
                logger.info("Stopping bot...")
                updater.stop()
            queue_service.stop_workers()
            logger.info("Bot stopped gracefully")
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {cleanup_error}")


if __name__ == "__main__":
    main()
