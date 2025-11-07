"""
Interactive Quiz Service
מבחן אינטראקטיבי בטלגרם
"""
import time
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

from services.session_service import session_service
from services.generator_service import Question
from utils.logger import logger


@dataclass
class QuizSession:
    """סשן מבחן אינטראקטיבי"""
    chat_id: int
    questions: List[Question]
    current_question: int = 0
    correct_answers: int = 0
    user_answers: List[int] = None
    start_time: datetime = None
    end_time: Optional[datetime] = None
    is_active: bool = True
    
    def __post_init__(self):
        if self.user_answers is None:
            self.user_answers = []
        if self.start_time is None:
            self.start_time = datetime.now()


class InteractiveQuizService:
    """Service for interactive Telegram quizzes"""
    
    def __init__(self):
        """Initialize quiz service"""
        self.active_quizzes: Dict[int, QuizSession] = {}
        logger.info("Interactive quiz service initialized")
    
    def start_quiz(self, chat_id: int, questions: List[Question], max_questions: int = None) -> Optional[QuizSession]:
        """
        התחלת מבחן אינטראקטיבי
        
        Args:
            chat_id: מזהה צ'אט
            questions: רשימת שאלות
            max_questions: מקסימום שאלות (אופציונלי - לקיצור מבחן ארוך)
        
        Returns:
            QuizSession או None
        """
        try:
            # אם יש מבחן פעיל - נפסיק אותו
            if chat_id in self.active_quizzes:
                logger.info(f"Stopping existing quiz for chat_id={chat_id}")
                self.stop_quiz(chat_id)
            
            # הגבלת מספר שאלות למקסימום 20 למבחן אינטראקטיבי
            if max_questions:
                max_questions = min(max_questions, 20)
            else:
                max_questions = min(len(questions), 20)
            
            # ערבוב ובחירת שאלות
            quiz_questions = random.sample(questions, min(len(questions), max_questions))
            
            # יצירת סשן
            quiz_session = QuizSession(
                chat_id=chat_id,
                questions=quiz_questions,
                current_question=0,
                correct_answers=0,
                user_answers=[],
                start_time=datetime.now(),
                is_active=True
            )
            
            self.active_quizzes[chat_id] = quiz_session
            
            logger.info(f"Started interactive quiz for chat_id={chat_id} with {len(quiz_questions)} questions")
            return quiz_session
            
        except Exception as e:
            logger.error(f"Failed to start quiz for chat_id={chat_id}: {e}")
            return None
    
    def get_quiz_session(self, chat_id: int) -> Optional[QuizSession]:
        """קבלת סשן מבחן פעיל"""
        return self.active_quizzes.get(chat_id)
    
    def submit_answer(self, chat_id: int, answer_index: int) -> Dict[str, Any]:
        """
        שליחת תשובה לשאלה נוכחית
        
        Args:
            chat_id: מזהה צ'אט
            answer_index: אינדקס התשובה (0-3)
        
        Returns:
            Dictionary with result info
        """
        try:
            quiz_session = self.active_quizzes.get(chat_id)
            if not quiz_session or not quiz_session.is_active:
                return {"success": False, "error": "No active quiz found"}
            
            current_q = quiz_session.questions[quiz_session.current_question]
            is_correct = answer_index == current_q.correct_index
            
            # שמירת התשובה
            quiz_session.user_answers.append(answer_index)
            
            if is_correct:
                quiz_session.correct_answers += 1
            
            # מעבר לשאלה הבאה
            quiz_session.current_question += 1
            
            # בדיקה אם המבחן הסתיים
            is_finished = quiz_session.current_question >= len(quiz_session.questions)
            
            if is_finished:
                quiz_session.end_time = datetime.now()
                quiz_session.is_active = False
            
            result = {
                "success": True,
                "is_correct": is_correct,
                "correct_answer": current_q.options[current_q.correct_index],
                "explanation": current_q.explanation,
                "is_finished": is_finished,
                "current_score": quiz_session.correct_answers,
                "total_questions": len(quiz_session.questions),
                "current_question": quiz_session.current_question
            }
            
            if is_finished:
                result["final_stats"] = self._calculate_final_stats(quiz_session)
            
            logger.info(f"Answer submitted for chat_id={chat_id}, question {quiz_session.current_question-1}, correct={is_correct}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error submitting answer for chat_id={chat_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def stop_quiz(self, chat_id: int) -> bool:
        """עצירת מבחן פעיל"""
        try:
            if chat_id in self.active_quizzes:
                del self.active_quizzes[chat_id]
                logger.info(f"Stopped quiz for chat_id={chat_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error stopping quiz for chat_id={chat_id}: {e}")
            return False
    
    def _calculate_final_stats(self, quiz_session: QuizSession) -> Dict[str, Any]:
        """חישוב סטטיסטיקות סופיות"""
        try:
            total_questions = len(quiz_session.questions)
            correct_answers = quiz_session.correct_answers
            
            # ציון באחוזים
            score_percentage = (correct_answers / total_questions) * 100
            
            # זמן מבחן
            duration = quiz_session.end_time - quiz_session.start_time
            duration_minutes = duration.total_seconds() / 60
            
            # התפלגות קושי
            difficulty_stats = {}
            difficulty_correct = {}
            
            for i, question in enumerate(quiz_session.questions):
                difficulty = question.difficulty
                user_answer = quiz_session.user_answers[i]
                is_correct = user_answer == question.correct_index
                
                if difficulty not in difficulty_stats:
                    difficulty_stats[difficulty] = 0
                    difficulty_correct[difficulty] = 0
                
                difficulty_stats[difficulty] += 1
                if is_correct:
                    difficulty_correct[difficulty] += 1
            
            # דירוג ביצועים
            if score_percentage >= 90:
                grade = "מעולה! 🥇"
                grade_emoji = "🥇"
            elif score_percentage >= 80:
                grade = "טוב מאוד! 🥈"  
                grade_emoji = "🥈"
            elif score_percentage >= 70:
                grade = "טוב! 🥉"
                grade_emoji = "🥉"
            elif score_percentage >= 60:
                grade = "עובר 👍"
                grade_emoji = "👍"
            else:
                grade = "צריך שיפור 📚"
                grade_emoji = "📚"
            
            return {
                "total_questions": total_questions,
                "correct_answers": correct_answers,
                "wrong_answers": total_questions - correct_answers,
                "score_percentage": round(score_percentage, 1),
                "duration_minutes": round(duration_minutes, 1),
                "grade": grade,
                "grade_emoji": grade_emoji,
                "difficulty_stats": difficulty_stats,
                "difficulty_correct": difficulty_correct,
                "questions_per_minute": round(total_questions / duration_minutes, 1) if duration_minutes > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating final stats: {e}")
            return {
                "total_questions": len(quiz_session.questions),
                "correct_answers": quiz_session.correct_answers,
                "score_percentage": 0,
                "grade": "שגיאה בחישוב"
            }
    
    def cleanup_old_quizzes(self, max_age_hours: int = 2):
        """ניקוי מבחנים ישנים"""
        try:
            current_time = datetime.now()
            old_chats = []
            
            for chat_id, quiz_session in self.active_quizzes.items():
                age = current_time - quiz_session.start_time
                if age.total_seconds() > max_age_hours * 3600:
                    old_chats.append(chat_id)
            
            for chat_id in old_chats:
                del self.active_quizzes[chat_id]
                logger.info(f"Cleaned up old quiz for chat_id={chat_id}")
                
        except Exception as e:
            logger.error(f"Error cleaning up old quizzes: {e}")
    
    def get_active_quiz_count(self) -> int:
        """מספר מבחנים פעילים"""
        return len(self.active_quizzes)


# Global instance
interactive_quiz_service = InteractiveQuizService()