"""
HTML Renderer
יצירת quiz אינטראקטיבי בפורמט HTML
"""
import os
import json
from typing import List, Dict, Any
from datetime import datetime
from html import escape

from src.services.generator_service import Question
from src.config import config
from src.utils.logger import logger


class HTMLRenderer:
    """Service for rendering interactive HTML quizzes"""
    
    @staticmethod
    def render_quiz(questions: List[Question], metadata: Dict[str, Any]) -> str:
        """
        יצירת HTML quiz מוכן לשימוש
        
        Args:
            questions: רשימת Question objects
            metadata: מידע נוסף (filename, etc.)
        
        Returns:
            HTML string
        """
        filename = metadata.get("filename", "מבחן")
        question_count = len(questions)
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        # המרת שאלות ל-JSON (לשימוש ב-JavaScript)
        questions_json = json.dumps([
            {
                "id": q.id,
                "question": q.question,
                "options": q.options,
                "correct_index": q.correct_index,
                "difficulty": q.difficulty,
                "explanation": q.explanation
            }
            for q in questions
        ], ensure_ascii=False)
        
        html = f"""<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>מבחן - {escape(filename)}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: Arial, Tahoma, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            direction: rtl;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        header h1 {{
            font-size: 2em;
            margin-bottom: 10px;
        }}
        
        header p {{
            opacity: 0.9;
            font-size: 1.1em;
        }}
        
        .progress-bar {{
            background: rgba(255,255,255,0.2);
            height: 8px;
            margin-top: 20px;
            border-radius: 4px;
            overflow: hidden;
        }}
        
        .progress-fill {{
            background: #4CAF50;
            height: 100%;
            width: 0%;
            transition: width 0.3s ease;
        }}
        
        main {{
            padding: 30px;
        }}
        
        .question-card {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
            border: 2px solid transparent;
            transition: all 0.3s ease;
        }}
        
        .question-card.answered {{
            border-color: #667eea;
        }}
        
        .question-card.correct {{
            border-color: #4CAF50;
            background: #f1f8f4;
        }}
        
        .question-card.incorrect {{
            border-color: #f44336;
            background: #fef1f1;
        }}
        
        .question-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .question-number {{
            font-weight: bold;
            color: #667eea;
            font-size: 1.1em;
        }}
        
        .difficulty {{
            font-size: 0.85em;
            padding: 4px 10px;
            border-radius: 12px;
            font-weight: bold;
        }}
        
        .difficulty.easy {{
            background: #c8e6c9;
            color: #2e7d32;
        }}
        
        .difficulty.medium {{
            background: #fff9c4;
            color: #f57f17;
        }}
        
        .difficulty.hard {{
            background: #ffcdd2;
            color: #c62828;
        }}
        
        .question-text {{
            font-size: 1.2em;
            margin-bottom: 20px;
            color: #333;
            line-height: 1.6;
        }}
        
        .options {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        
        .option {{
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
        }}
        
        .option:hover:not(.disabled) {{
            border-color: #667eea;
            background: #f5f7ff;
            transform: translateX(-5px);
        }}
        
        .option.selected {{
            border-color: #667eea;
            background: #e8eaf6;
        }}
        
        .option.correct {{
            border-color: #4CAF50;
            background: #e8f5e9;
        }}
        
        .option.incorrect {{
            border-color: #f44336;
            background: #ffebee;
        }}
        
        .option.disabled {{
            cursor: not-allowed;
            opacity: 0.7;
        }}
        
        .option-label {{
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: #667eea;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-left: 15px;
            flex-shrink: 0;
        }}
        
        .option-text {{
            flex: 1;
        }}
        
        .explanation {{
            margin-top: 15px;
            padding: 15px;
            background: #fff3cd;
            border-right: 4px solid #ffc107;
            border-radius: 5px;
            display: none;
        }}
        
        .explanation.show {{
            display: block;
        }}
        
        .explanation strong {{
            color: #856404;
        }}
        
        footer {{
            padding: 30px;
            text-align: center;
            background: #f8f9fa;
        }}
        
        .submit-btn {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 1.2em;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: bold;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            margin: 10px;
        }}
        
        .submit-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        }}
        
        .submit-btn:disabled {{
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }}
        
        .reset-btn {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 1.2em;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: bold;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            margin: 10px;
        }}
        
        .reset-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        }}
        
        #results {{
            margin-top: 30px;
            display: none;
        }}
        
        .result-card {{
            background: white;
            border-radius: 10px;
            padding: 30px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .score {{
            font-size: 4em;
            font-weight: bold;
            color: #667eea;
            margin: 20px 0;
        }}
        
        .score.excellent {{
            color: #4CAF50;
        }}
        
        .score.good {{
            color: #FFC107;
        }}
        
        .score.poor {{
            color: #f44336;
        }}
        
        .result-text {{
            font-size: 1.5em;
            margin-bottom: 20px;
        }}
        
        .stats {{
            display: flex;
            justify-content: space-around;
            margin-top: 30px;
            flex-wrap: wrap;
            gap: 20px;
        }}
        
        .stat {{
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        
        @media (max-width: 600px) {{
            body {{
                padding: 10px;
            }}
            
            header h1 {{
                font-size: 1.5em;
            }}
            
            main {{
                padding: 15px;
            }}
            
            .question-text {{
                font-size: 1.1em;
            }}
            
            .score {{
                font-size: 3em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>מבחן אמריקאי</h1>
            <p>📄 מקור: {escape(filename)} | 📝 {question_count} שאלות | 📅 {timestamp}</p>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
        </header>
        
        <main id="quiz">
            <!-- השאלות ייווצרו דינמית ב-JavaScript -->
        </main>
        
        <footer>
            <button class="submit-btn" id="submitBtn" onclick="submitQuiz()">
                ✅ שלח תשובות ובדוק ציון
            </button>
            <button class="reset-btn" id="resetBtn" onclick="resetQuiz()">
                🔄 אפס תשובות
            </button>
            
            <div id="results">
                <div class="result-card">
                    <h2>תוצאות המבחן</h2>
                    <div class="score" id="scoreDisplay">0%</div>
                    <div class="result-text" id="resultText"></div>
                    <div class="stats">
                        <div class="stat">
                            <div class="stat-value" id="correctCount">0</div>
                            <div class="stat-label">תשובות נכונות</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" id="incorrectCount">0</div>
                            <div class="stat-label">תשובות שגויות</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" id="unansweredCount">0</div>
                            <div class="stat-label">לא נענו</div>
                        </div>
                    </div>
                </div>
            </div>
        </footer>
    </div>
    
    <script>
        // נתוני השאלות
        const questions = {questions_json};
        
        // מעקב אחרי תשובות
        const userAnswers = {{}};
        let quizSubmitted = false;
        
        // טעינת השאלות
        function loadQuiz() {{
            const quizContainer = document.getElementById('quiz');
            
            questions.forEach((q, index) => {{
                const card = document.createElement('div');
                card.className = 'question-card';
                card.id = `question-${{q.id}}`;
                
                const difficultyText = {{
                    'easy': 'קל',
                    'medium': 'בינוני',
                    'hard': 'קשה',
                    'very_hard': 'קשה מאוד',
                }}[q.difficulty] || q.difficulty;
                
                card.innerHTML = `
                    <div class="question-header">
                        <span class="question-number">שאלה ${{index + 1}}</span>
                        <span class="difficulty ${{q.difficulty}}">${{difficultyText}}</span>
                    </div>
                    <div class="question-text">${{q.question}}</div>
                    <div class="options">
                        ${{q.options.map((opt, i) => `
                            <div class="option" onclick="selectAnswer('${{q.id}}', ${{i}})">
                                <div class="option-label">${{String.fromCharCode(65 + i)}}</div>
                                <div class="option-text">${{opt}}</div>
                            </div>
                        `).join('')}}
                    </div>
                    <div class="explanation" id="explanation-${{q.id}}">
                        <strong>💡 הסבר:</strong> ${{q.explanation}}
                    </div>
                `;
                
                quizContainer.appendChild(card);
            }});
        }}
        
        // בחירת תשובה
        function selectAnswer(questionId, optionIndex) {{
            if (quizSubmitted) return;
            
            userAnswers[questionId] = optionIndex;
            
            // עדכון UI
            const card = document.getElementById(`question-${{questionId}}`);
            const options = card.querySelectorAll('.option');
            
            options.forEach((opt, i) => {{
                opt.classList.remove('selected');
                if (i === optionIndex) {{
                    opt.classList.add('selected');
                }}
            }});
            
            card.classList.add('answered');
            updateProgress();
        }}
        
        // עדכון progress bar
        function updateProgress() {{
            const answered = Object.keys(userAnswers).length;
            const total = questions.length;
            const percentage = (answered / total) * 100;
            
            document.getElementById('progressFill').style.width = percentage + '%';
            
            // אפשר submit תמיד (גם אם לא ענו על הכל)
            const submitBtn = document.getElementById('submitBtn');
            submitBtn.disabled = false;
        }}
        
        // שליחת המבחן
        function submitQuiz() {{
            if (quizSubmitted) return;
            
            // בדיקה אם המשתמש ענה על לפחות שאלה אחת
            if (Object.keys(userAnswers).length === 0) {{
                alert('⚠️ עליך לענות לפחות על שאלה אחת!');
                return;
            }}
            
            // אישור אם יש שאלות שלא נענו
            const unansweredQuestions = questions.length - Object.keys(userAnswers).length;
            if (unansweredQuestions > 0) {{
                const confirmed = confirm(`⚠️ יש ${{unansweredQuestions}} שאלות שלא נענו.\\n\\nשאלות שלא נענו יסומנו כשגויות.\\n\\nלהמשיך?`);
                if (!confirmed) return;
            }}
            
            quizSubmitted = true;
            
            let correct = 0;
            let incorrect = 0;
            let unanswered = 0;
            
            questions.forEach(q => {{
                const card = document.getElementById(`question-${{q.id}}`);
                const options = card.querySelectorAll('.option');
                const userAnswer = userAnswers[q.id];
                
                // נעילת כל האפשרויות
                options.forEach(opt => opt.classList.add('disabled'));
                
                if (userAnswer === undefined) {{
                    unanswered++;
                    card.classList.add('incorrect');
                    // הדגשת התשובה הנכונה
                    options[q.correct_index].classList.add('correct');
                }} else if (userAnswer === q.correct_index) {{
                    correct++;
                    card.classList.add('correct');
                    options[userAnswer].classList.add('correct');
                }} else {{
                    incorrect++;
                    card.classList.add('incorrect');
                    options[userAnswer].classList.add('incorrect');
                    options[q.correct_index].classList.add('correct');
                }}
                
                // הצגת הסבר
                document.getElementById(`explanation-${{q.id}}`).classList.add('show');
            }});
            
            // חישוב ציון - רק מהשאלות שנענו
            const answeredQuestions = questions.length - unanswered;
            const score = answeredQuestions > 0 ? Math.round((correct / answeredQuestions) * 100) : 0;
            
            // הצגת תוצאות
            displayResults(score, correct, incorrect, unanswered);
            
            // גלילה לתוצאות
            document.getElementById('results').scrollIntoView({{ behavior: 'smooth' }});
        }}
        
        // הצגת תוצאות
        function displayResults(score, correct, incorrect, unanswered) {{
            const resultsDiv = document.getElementById('results');
            const scoreDisplay = document.getElementById('scoreDisplay');
            const resultText = document.getElementById('resultText');
            
            scoreDisplay.textContent = score + '%';
            
            // צביעה לפי ציון
            scoreDisplay.className = 'score';
            if (score >= 85) {{
                scoreDisplay.classList.add('excellent');
                resultText.textContent = '🎉 מצוין! ציון מעולה!';
            }} else if (score >= 70) {{
                scoreDisplay.classList.add('good');
                resultText.textContent = '👍 יפה מאוד! המשך כך!';
            }} else {{
                scoreDisplay.classList.add('poor');
                resultText.textContent = '💪 כדאי לחזור על החומר';
            }}
            
            document.getElementById('correctCount').textContent = correct;
            document.getElementById('incorrectCount').textContent = incorrect;
            document.getElementById('unansweredCount').textContent = unanswered;
            
            resultsDiv.style.display = 'block';
            
            // הסתרת כפתורים
            document.getElementById('submitBtn').style.display = 'none';
            document.getElementById('resetBtn').style.display = 'none';
        }}
        
        // איפוס המבחן
        function resetQuiz() {{
            if (!confirm('🔄 האם אתה בטוח שברצונך לאפס את כל התשובות ולהתחיל מחדש?')) {{
                return;
            }}
            
            // איפוס משתנים
            Object.keys(userAnswers).forEach(key => delete userAnswers[key]);
            quizSubmitted = false;
            
            // איפוס כל הכרטיסים
            questions.forEach(q => {{
                const card = document.getElementById(`question-${{q.id}}`);
                const options = card.querySelectorAll('.option');
                
                // הסרת כל הclasses
                card.className = 'question-card';
                options.forEach(opt => {{
                    opt.className = 'option';
                }});
                
                // הסתרת הסברים
                document.getElementById(`explanation-${{q.id}}`).classList.remove('show');
            }});
            
            // איפוס progress
            document.getElementById('progressFill').style.width = '0%';
            
            // הסתרת תוצאות
            document.getElementById('results').style.display = 'none';
            
            // הצגת כפתורים
            document.getElementById('submitBtn').style.display = 'inline-block';
            document.getElementById('submitBtn').disabled = false;
            document.getElementById('resetBtn').style.display = 'inline-block';
            
            // גלילה לראש
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}
        
        // טעינה ראשונית
        window.addEventListener('DOMContentLoaded', loadQuiz);
    </script>
</body>
</html>"""
        
        return html
    
    @staticmethod
    def save_quiz(html_content: str, chat_id: int, job_id: str) -> str:
        """
        שמירת HTML לקובץ
        
        Args:
            html_content: תוכן ה-HTML
            chat_id: Telegram chat ID
            job_id: מזהה job
        
        Returns:
            נתיב לקובץ שנשמר
        """
        try:
            filename = f"quiz_{chat_id}_{job_id}.html"
            filepath = os.path.join(config.OUTPUTS_DIR, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Saved quiz to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save quiz: {e}")
            return ""


# Global instance
html_renderer = HTMLRenderer()
