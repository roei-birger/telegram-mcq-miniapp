"""
Queue Service
ניהול תור עבודות רקע ב-Redis
"""
import redis
import json
import time
import threading
from typing import Optional, Dict, Any
from datetime import datetime

from config import config
from utils.logger import logger
from services.generator_service import generator_service
from services.html_renderer import html_renderer


class QueueService:
    """Service for managing background job processing"""
    
    def __init__(self):
        """Initialize Redis connection for queue"""
        try:
            self.redis_client = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Queue service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize queue service: {e}")
            raise
        
        self.workers = []
        self.is_running = False
    
    # ==================== Job Management ====================
    
    def add_job(self, chat_id: int, text: str, question_count: int, metadata: Dict[str, Any], file_info: Optional[Dict[str, Any]] = None) -> str:
        """
        הוספת job לתור
        
        Args:
            chat_id: Telegram chat ID
            text: הטקסט המקור
            question_count: מספר שאלות
            metadata: מידע נוסף
            file_info: מידע על הקבצים (אופציונלי) - עבור מספר קבצים
        
        Returns:
            job_id
        """
        try:
            job_id = f"job_{chat_id}_{int(time.time())}"
            
            job_data = {
                "job_id": job_id,
                "chat_id": str(chat_id),
                "text": text,
                "question_count": question_count,
                "metadata": metadata,
                "file_info": file_info,
                "status": "PENDING",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # שמירת job data
            job_key = f"job:{job_id}"
            self.redis_client.setex(
                job_key,
                config.JOB_TIMEOUT,
                json.dumps(job_data)
            )
            
            # הוספה לתור
            self.redis_client.rpush("job_queue", job_id)
            
            logger.info(f"Added job {job_id} to queue")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to add job: {e}")
            return ""
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        קבלת status של job
        
        Args:
            job_id: מזהה job
        
        Returns:
            Job data או None
        """
        try:
            job_key = f"job:{job_id}"
            job_json = self.redis_client.get(job_key)
            
            if job_json:
                return json.loads(job_json)
            return None
        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            return None
    
    def update_job_status(self, job_id: str, status: str, output_file: str = None, error: str = None) -> bool:
        """
        עדכון status של job
        
        Args:
            job_id: מזהה job
            status: סטטוס חדש (PROCESSING, COMPLETED, FAILED)
            output_file: נתיב לקובץ פלט (אופציונלי)
            error: הודעת שגיאה (אופציונלי)
        
        Returns:
            True if successful
        """
        try:
            job = self.get_job_status(job_id)
            if not job:
                return False
            
            job["status"] = status
            job["updated_at"] = datetime.now().isoformat()
            
            if output_file:
                job["output_file"] = output_file
            
            if error:
                job["error"] = error
            
            job_key = f"job:{job_id}"
            self.redis_client.setex(
                job_key,
                config.JOB_TIMEOUT,
                json.dumps(job)
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to update job status: {e}")
            return False
    
    # ==================== Background Workers ====================
    
    def start_workers(self, num_workers: int = 3):
        """
        הפעלת workers לעיבוד רקע
        
        Args:
            num_workers: מספר workers במקביל
        """
        if self.is_running:
            logger.warning("Workers already running")
            return
        
        self.is_running = True
        
        for i in range(num_workers):
            worker_thread = threading.Thread(
                target=self._worker_loop,
                args=(i,),
                daemon=True
            )
            worker_thread.start()
            self.workers.append(worker_thread)
        
        logger.info(f"Started {num_workers} background workers")
    
    def stop_workers(self):
        """עצירת workers"""
        self.is_running = False
        logger.info("Stopping workers...")
    
    def _worker_loop(self, worker_id: int):
        """
        לולאת worker - מעבד jobs מהתור
        
        Args:
            worker_id: מזהה worker
        """
        logger.info(f"Worker {worker_id} started")
        
        while self.is_running:
            try:
                # משיכת job מהתור (עם timeout)
                result = self.redis_client.blpop("job_queue", timeout=5)
                
                if not result:
                    continue
                
                _, job_id = result
                logger.info(f"Worker {worker_id} processing {job_id}")
                
                # עיבוד ה-job
                self._process_job(job_id)
                
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                time.sleep(1)
        
        logger.info(f"Worker {worker_id} stopped")
    
    def _process_job(self, job_id: str):
        """
        עיבוד job בודד
        
        Args:
            job_id: מזהה job
        """
        try:
            # קבלת job data
            job = self.get_job_status(job_id)
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            chat_id = job["chat_id"]
            text = job["text"]
            question_count = job["question_count"]
            metadata = job.get("metadata", {})
            file_info = job.get("file_info")
            
            # עדכון סטטוס ל-PROCESSING
            self.update_job_status(job_id, "PROCESSING")
            
            # יצירת שאלות עם Gemini
            logger.info(f"Generating {question_count} questions for {job_id}")
            questions = generator_service.generate_questions(text, question_count, file_info)
            
            if not questions:
                self.update_job_status(job_id, "FAILED", error="Failed to generate questions")
                return
            
            # יצירת HTML
            logger.info(f"Rendering HTML for {job_id}")
            html_content = html_renderer.render_quiz(questions, metadata)
            
            # שמירת HTML לקובץ
            output_file = html_renderer.save_quiz(html_content, chat_id, job_id)
            
            if not output_file:
                self.update_job_status(job_id, "FAILED", error="Failed to save HTML file")
                return
            
            # עדכון סטטוס ל-COMPLETED
            self.update_job_status(job_id, "COMPLETED", output_file=output_file)
            logger.info(f"Job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to process job {job_id}: {e}")
            self.update_job_status(job_id, "FAILED", error=str(e))


# Global instance
queue_service = QueueService()
