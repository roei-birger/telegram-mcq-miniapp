"""
Session Service
ניהול sessions של משתמשים ב-Redis
"""
import redis
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from src.config import config
from src.utils.logger import logger


class SessionService:
    """
    Service for managing user sessions in Redis
    """
    
    def __init__(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {config.REDIS_HOST}:{config.REDIS_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    # ==================== Session Management ====================
    
    def create_session(self, chat_id: int) -> bool:
        """
        יצירת session חדשה למשתמש
        
        Args:
            chat_id: Telegram chat ID
        
        Returns:
            True if successful
        """
        try:
            session_key = f"session:{chat_id}"
            session_data = {
                "chat_id": str(chat_id),
                "state": "START",
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(seconds=config.SESSION_TTL)).isoformat()
            }
            
            self.redis_client.setex(
                session_key,
                config.SESSION_TTL,
                json.dumps(session_data)
            )
            
            logger.info(f"Created session for chat_id={chat_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return False
    
    def get_session(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """
        קבלת session קיימת
        
        Args:
            chat_id: Telegram chat ID
        
        Returns:
            Session data או None אם לא קיים
        """
        try:
            session_key = f"session:{chat_id}"
            session_json = self.redis_client.get(session_key)
            
            if session_json:
                return json.loads(session_json)
            return None
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return None
    
    def update_session_state(self, chat_id: int, state: str) -> bool:
        """
        עדכון state של session
        
        Args:
            chat_id: Telegram chat ID
            state: המצב החדש (START, AWAITING_FILE, AWAITING_COUNT, etc.)
        
        Returns:
            True if successful
        """
        try:
            session = self.get_session(chat_id)
            if not session:
                return False
            
            session["state"] = state
            session_key = f"session:{chat_id}"
            
            # שמירה עם TTL מחודש
            self.redis_client.setex(
                session_key,
                config.SESSION_TTL,
                json.dumps(session)
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to update session state: {e}")
            return False
    
    def delete_session(self, chat_id: int) -> bool:
        """מחיקת session"""
        try:
            session_key = f"session:{chat_id}"
            self.redis_client.delete(session_key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False
    
    # ==================== Rate Limiting ====================
    
    def check_rate_limit(self, chat_id: int) -> tuple[bool, str]:
        """
        בדיקת rate limiting
        
        Args:
            chat_id: Telegram chat ID
        
        Returns:
            (is_allowed, error_message)
        """
        try:
            # Short-term limit (10 minutes)
            short_key = f"rate_limit:{chat_id}:short"
            short_count = self.redis_client.get(short_key)
            
            if short_count and int(short_count) >= config.RATE_LIMIT_PER_10MIN:
                ttl = self.redis_client.ttl(short_key)
                minutes = ttl // 60
                return False, f"⏳ חרגת מהמכסה ({config.RATE_LIMIT_PER_10MIN} בקשות / 10 דקות). נסה שוב בעוד {minutes + 1} דקות."
            
            # Long-term limit (24 hours)
            long_key = f"rate_limit:{chat_id}:long"
            long_count = self.redis_client.get(long_key)
            
            if long_count and int(long_count) >= config.RATE_LIMIT_PER_DAY:
                ttl = self.redis_client.ttl(long_key)
                hours = ttl // 3600
                return False, f"⏳ חרגת מהמכסה היומית ({config.RATE_LIMIT_PER_DAY} בקשות / יום). נסה שוב בעוד {hours + 1} שעות."
            
            return True, ""
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True, ""  # במקרה של שגיאה, נאפשר
    
    def increment_rate_limit(self, chat_id: int) -> bool:
        """
        הגדלת מונה rate limiting
        
        Args:
            chat_id: Telegram chat ID
        
        Returns:
            True if successful
        """
        try:
            # Short-term counter
            short_key = f"rate_limit:{chat_id}:short"
            pipe = self.redis_client.pipeline()
            pipe.incr(short_key)
            pipe.expire(short_key, 600)  # 10 minutes
            
            # Long-term counter
            long_key = f"rate_limit:{chat_id}:long"
            pipe.incr(long_key)
            pipe.expire(long_key, 86400)  # 24 hours
            
            pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Failed to increment rate limit: {e}")
            return False
    
    # ==================== File Data Storage ====================
    
    def save_file_data(self, chat_id: int, file_data: Dict[str, Any]) -> bool:
        """
        שמירת metadata של קובץ שהועלה
        
        Args:
            chat_id: Telegram chat ID
            file_data: מטא-דאטה של הקובץ
        
        Returns:
            True if successful
        """
        try:
            file_key = f"file_data:{chat_id}"
            file_data["uploaded_at"] = datetime.now().isoformat()
            
            self.redis_client.setex(
                file_key,
                config.FILE_DATA_TTL,  # 72 hours
                json.dumps(file_data)
            )
            
            logger.info(f"Saved file data for chat_id={chat_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save file data: {e}")
            return False
    
    def get_file_data(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """
        קבלת file data
        
        Args:
            chat_id: Telegram chat ID
        
        Returns:
            File data או None
        """
        try:
            file_key = f"file_data:{chat_id}"
            file_json = self.redis_client.get(file_key)
            
            if file_json:
                return json.loads(file_json)
            return None
        except Exception as e:
            logger.error(f"Failed to get file data: {e}")
            return None
    
    def delete_file_data(self, chat_id: int) -> bool:
        """מחיקת file data"""
        try:
            file_key = f"file_data:{chat_id}"
            self.redis_client.delete(file_key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete file data: {e}")
            return False


# Global instance
session_service = SessionService()
