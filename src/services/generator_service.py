"""
Generator Service
יצירת שאלות באמצעות Google Gemini
"""
import json
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import google.generativeai as genai

from src.config import config
from src.utils.logger import logger


@dataclass
class Question:
    """מבנה נתונים של שאלה"""
    id: str
    question: str
    options: List[str]  # 4 אפשרויות
    correct_index: int  # 0-3
    difficulty: str  # easy/medium/hard
    explanation: str


class GeneratorService:
    """Service for generating MCQ questions using Gemini"""
    
    def __init__(self):
        """Initialize Gemini API"""
        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(config.GEMINI_MODEL)
            logger.info(f"Using Google Gemini ({config.GEMINI_MODEL})")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            raise
    
    def generate_questions(self, text: str, count: int, file_info: Optional[Dict[str, Any]] = None) -> Optional[List[Question]]:
        """
        יצירת שאלות אמריקאיות מטקסט
        
        Args:
            text: הטקסט המקור (יכול להיות טקסט מאוחד ממספר קבצים)
            count: מספר שאלות רצוי
            file_info: מידע על הקבצים (אופציונלי) - עבור מספר קבצים
        
        Returns:
            רשימת Question objects או None במקרה של כשל
        """
        # אם יש מספר קבצים, נקצה שאלות באופן יחסי
        if file_info and "files" in file_info and len(file_info["files"]) > 1:
            return self._generate_questions_multi_file(file_info["files"], count)
        
        # אחרת, יצירה רגילה מטקסט מאוחד
        return self._generate_questions_single(text, count)
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # בניית prompt
                prompt = self._build_prompt(text, count)
                
                logger.info(f"Generating {count} questions with Gemini (attempt {attempt + 1}/{max_retries})...")
                
                # קריאה ל-Gemini
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,
                        max_output_tokens=4096,  # הגדלנו כדי למנוע קיטוע
                    )
                )
                
                # Parsing התשובה
                questions = self._parse_response(response.text, count)
                
                if not questions:
                    if attempt < max_retries - 1:
                        logger.warning(f"Parse failed, retrying... ({attempt + 1}/{max_retries})")
                        continue
                    logger.error("Failed to parse Gemini response after all retries")
                    return None
                
                # Validation
                if not self._validate_questions(questions, count):
                    if attempt < max_retries - 1:
                        logger.warning(f"Validation failed, retrying... ({attempt + 1}/{max_retries})")
                        continue
                    logger.error("Generated questions failed validation after all retries")
                    return None
                
                # ערבוב אפשרויות
                questions = self._shuffle_options(questions)
                
                logger.info(f"Successfully generated {len(questions)} questions")
                return questions
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying...")
                    continue
                logger.error(f"Question generation failed after all retries: {e}")
                return None
        
        return None
    
    def _generate_questions_multi_file(self, files: List[Dict[str, Any]], total_count: int) -> Optional[List[Question]]:
        """
        יצירת שאלות ממספר קבצים באופן יחסי לגודל כל קובץ
        
        Args:
            files: רשימת קבצים עם text, word_count, filename
            total_count: סה"כ שאלות רצויות
        
        Returns:
            רשימת Question objects מאוחדת או None
        """
        try:
            logger.info(f"Generating {total_count} questions from {len(files)} files proportionally")
            
            # חישוב סה"כ מילים
            total_words = sum(f["word_count"] for f in files)
            
            # חישוב כמות שאלות לכל קובץ באופן יחסי
            questions_per_file = []
            remaining_questions = total_count
            
            for i, file in enumerate(files):
                if i == len(files) - 1:
                    # הקובץ האחרון מקבל את השאר (לפחות 1)
                    file_questions = max(1, remaining_questions)
                else:
                    # חישוב יחסי
                    ratio = file["word_count"] / total_words
                    file_questions = max(1, round(total_count * ratio))  # לפחות שאלה אחת
                    remaining_questions -= file_questions
                
                # אם נגמרו השאלות, תן לפחות 1
                if remaining_questions < 0:
                    remaining_questions = 0
                
                questions_per_file.append({
                    "file": file,
                    "count": file_questions,
                    "percentage": (file["word_count"] / total_words) * 100
                })
                
                logger.info(f"  {file['filename']}: {file_questions} שאלות ({file['word_count']:,} מילים, {(file['word_count']/total_words)*100:.1f}%)")
            
            # יצירת שאלות מכל קובץ
            all_questions = []
            for item in questions_per_file:
                file = item["file"]
                count = item["count"]
                
                # דילוג על קבצים עם 0 שאלות
                if count == 0:
                    logger.info(f"Skipping '{file['filename']}' (0 questions allocated)")
                    continue
                
                logger.info(f"Generating {count} questions from '{file['filename']}'...")
                
                # יצירת שאלות לקובץ זה
                questions = self._generate_questions_single(
                    text=file["text"],
                    count=count,
                    file_context=file["filename"]
                )
                
                if questions:
                    all_questions.extend(questions)
                    logger.info(f"  ✓ Got {len(questions)} questions from '{file['filename']}'")
                else:
                    logger.warning(f"  ✗ Failed to generate questions from '{file['filename']}'")
            
            if not all_questions:
                logger.error("Failed to generate any questions from any file")
                return None
            
            # ערבוב סדר השאלות כך שלא יהיו מקובצות לפי קובץ
            random.shuffle(all_questions)
            
            # עדכון IDs לפי סדר חדש
            for idx, q in enumerate(all_questions):
                q.id = f"q_{idx + 1}"
            
            logger.info(f"Successfully generated {len(all_questions)} questions from {len(files)} files")
            return all_questions
            
        except Exception as e:
            logger.error(f"Multi-file question generation failed: {e}")
            return None
    
    def _generate_questions_single(self, text: str, count: int, file_context: Optional[str] = None) -> Optional[List[Question]]:
        """
        יצירת שאלות מטקסט בודד
        
        Args:
            text: הטקסט המקור
            count: מספר שאלות רצוי
            file_context: שם הקובץ (אופציונלי)
        
        Returns:
            רשימת Question objects או None במקרה של כשל
        """
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # בניית prompt
                prompt = self._build_prompt(text, count, file_context)
                
                logger.info(f"Generating {count} questions with Gemini (attempt {attempt + 1}/{max_retries})...")
                
                # קריאה ל-Gemini
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,
                        max_output_tokens=4096,
                    )
                )
                
                # Parsing התשובה
                questions = self._parse_response(response.text, count)
                
                if not questions:
                    if attempt < max_retries - 1:
                        logger.warning(f"Parse failed, retrying... ({attempt + 1}/{max_retries})")
                        continue
                    logger.error("Failed to parse Gemini response after all retries")
                    return None
                
                # Validation
                if not self._validate_questions(questions, count):
                    if attempt < max_retries - 1:
                        logger.warning(f"Validation failed, retrying... ({attempt + 1}/{max_retries})")
                        continue
                    logger.error("Generated questions failed validation after all retries")
                    return None
                
                # ערבוב אפשרויות
                questions = self._shuffle_options(questions)
                
                logger.info(f"Successfully generated {len(questions)} questions")
                return questions
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying...")
                    continue
                logger.error(f"Question generation failed after all retries: {e}")
                return None
        
        return None
    
    def _build_prompt(self, text: str, count: int, file_context: Optional[str] = None) -> str:
        """
        בניית prompt ל-Gemini
        
        Args:
            text: הטקסט המקור
            count: מספר שאלות
            file_context: שם הקובץ (אופציונלי)
        
        Returns:
            Prompt string
        """
        # חיתוך טקסט ארוך מדי (Gemini context limit)
        max_chars = 40000
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
            logger.warning(f"Text truncated to {max_chars} characters")
        
        file_note = f"\n(טקסט מקובץ: {file_context})\n" if file_context else ""
        
        prompt = f"""אתה מומחה ליצירת שאלות בחירה מרובה (MCQ) בעברית.

צור בדיוק {count} שאלות מהטקסט הבא:{file_note}

{text}

דרישות חשובות:
1. כל שאלה חייבת להכיל בדיוק 4 אפשרויות תשובה
2. רק תשובה אחת נכונה
3. התפלגות קושי: 10% קלות (easy), 20% בינוניות (medium), 40% קשות (hard), 30% מאוד קשות (very_hard)
4. כל התוכן בעברית בלבד
5. השאלות חייבות להתבסס רק על הידע המופיע בטקסט
6. השאלות צריכות להיות ברורות וחד-משמעיות
7. התשובות השגויות צריכות להיות סבירות (distractors טובים)

**חשוב מאוד**: החזר רק JSON תקין ומושלם, ללא טקסט נוסף לפני או אחרי.
וודא שכל המחרוזות סגורות כראוי עם גרשיים.

פורמט JSON (חובה!):
{{
  "questions": [
    {{
      "question": "שאלה כאן",
      "options": ["תשובה 1", "תשובה 2", "תשובה 3", "תשובה 4"],
      "correct_index": 0,
      "difficulty": "medium",
      "explanation": "הסבר כאן"
    }}
  ]
}}

החזר רק את ה-JSON, שום דבר אחר."""
        
        return prompt
    
    def _parse_response(self, response_text: str, expected_count: int) -> Optional[List[Question]]:
        """
        Parsing של תשובת Gemini
        
        Args:
            response_text: התשובה מ-Gemini
            expected_count: מספר שאלות צפוי
        
        Returns:
            רשימת Question objects או None
        """
        try:
            # ניסיון לחלץ JSON מתוך הטקסט
            # לפעמים Gemini מוסיף ```json ... ```
            text = response_text.strip()
            
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            # ניקוי תווים בעייתיים
            text = text.replace('\n', ' ').replace('\r', '')
            
            # ניסיון ראשון - parse רגיל
            try:
                data = json.loads(text)
            except json.JSONDecodeError as e:
                # ניסיון שני - נסה למצוא את ה-JSON המלא
                logger.warning(f"First parse failed: {e}, trying to extract valid JSON...")
                
                # חיפוש אחר { ... } החיצוני
                start_idx = text.find('{')
                if start_idx == -1:
                    raise ValueError("No JSON object found")
                
                # נסה למצוא את ה-} הסוגר
                brace_count = 0
                end_idx = -1
                for i in range(start_idx, len(text)):
                    if text[i] == '{':
                        brace_count += 1
                    elif text[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                
                if end_idx == -1:
                    raise ValueError("Incomplete JSON object")
                
                text = text[start_idx:end_idx]
                data = json.loads(text)
            
            if "questions" not in data:
                logger.error("Response missing 'questions' field")
                return None
            
            questions = []
            for idx, q_data in enumerate(data["questions"]):
                try:
                    # וידוא שיש את כל השדות הנדרשים
                    if not all(key in q_data for key in ["question", "options", "correct_index"]):
                        logger.warning(f"Question {idx + 1} missing required fields")
                        continue
                    
                    # וידוא 4 אפשרויות
                    if len(q_data["options"]) != 4:
                        logger.warning(f"Question {idx + 1} has {len(q_data['options'])} options instead of 4")
                        continue
                    
                    question = Question(
                        id=f"q_{idx + 1}",
                        question=str(q_data["question"]).strip(),
                        options=[str(opt).strip() for opt in q_data["options"]],
                        correct_index=int(q_data["correct_index"]),
                        difficulty=q_data.get("difficulty", "medium"),
                        explanation=str(q_data.get("explanation", "")).strip()
                    )
                    questions.append(question)
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"Question {idx + 1} parsing error: {e}")
                    continue
            
            if len(questions) == 0:
                logger.error("No valid questions parsed")
                return None
            
            logger.info(f"Parsed {len(questions)} valid questions out of {len(data.get('questions', []))} total")
            return questions
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.debug(f"Response text (first 1000 chars): {response_text[:1000]}")
            return None
        except Exception as e:
            logger.error(f"Parsing error: {e}")
            return None
    
    def _validate_questions(self, questions: List[Question], expected_count: int) -> bool:
        """
        אימות תקינות השאלות
        
        Args:
            questions: רשימת שאלות
            expected_count: מספר שאלות צפוי
        
        Returns:
            True אם תקין
        """
        if not questions:
            return False
        
        # לפחות 80% מהשאלות המבוקשות
        min_questions = int(expected_count * 0.8)
        if len(questions) < min_questions:
            logger.warning(f"Got {len(questions)} questions, expected at least {min_questions}")
            return False
        
        # בדיקת כל שאלה
        for q in questions:
            # חובה: 4 אפשרויות
            if len(q.options) != 4:
                logger.warning(f"Question '{q.question[:30]}...' has {len(q.options)} options instead of 4")
                return False
            
            # correct_index בטווח
            if not (0 <= q.correct_index <= 3):
                logger.warning(f"Question '{q.question[:30]}...' has invalid correct_index: {q.correct_index}")
                return False
            
            # difficulty תקין
            if q.difficulty not in ["easy", "medium", "hard", "very_hard"]:
                logger.warning(f"Question '{q.question[:30]}...' has invalid difficulty: {q.difficulty}")
                q.difficulty = "medium"  # default
        
        return True
    
    def _shuffle_options(self, questions: List[Question]) -> List[Question]:
        """
        ערבוב אקראי של אפשרויות התשובה
        
        Args:
            questions: רשימת שאלות
        
        Returns:
            רשימת שאלות עם אפשרויות מעורבבות
        """
        for q in questions:
            # שמירת התשובה הנכונה
            correct_answer = q.options[q.correct_index]
            
            # Fisher-Yates shuffle
            random.shuffle(q.options)
            
            # עדכון correct_index
            q.correct_index = q.options.index(correct_answer)
        
        return questions


# Global instance
generator_service = GeneratorService()
