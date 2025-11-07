# 🤖 Telegram MCQ Bot - Python Edition

**בוט טלגרם + ממשק אינטרנטי ליצירת מבחני בחירה מרובה (MCQ) באמצעות AI**

מקבל קבצי PDF/DOCX/TXT ומייצר שאלות אמריקאיות בעברית עם Google Gemini.

🆕 **חדש!** ממשק אינטרנטי מלא בנוסף לבוט הטלגרם

---

## ✨ תכונות

### 🌐 **ממשק אינטרנטי (חדש!)**
- **דפדפן**: גישה דרך http://localhost:10000  
- **עיצוב מקצועי**: Bootstrap עם תמיכה מלאה בעברית (RTL)
- **העלאת קבצים**: Drag & Drop עם תמיכה במספר קבצים
- **הורדת מבחנים**: שמירה כ-HTML או הדפסה
- **רספונסיבי**: עובד על מחשב וסמארטפון

### 📱 **בוט טלגרם (מקורי)**
- 📄 **תמיכה בקבצים**: PDF, DOCX, TXT
- 🤖 **AI מתקדם**: Google Gemini (חינמי!)
- 📊 **HTML Quiz**: קובץ HTML מעוצב עם RTL, נגישות
- 🔒 **Rate Limiting**: הגבלת שימוש למשתמש
- 📝 **3-50 שאלות** לפי בחירה
- 🎯 **התפלגות קושי**: 40% קל, 40% בינוני, 20% קשה
- 💾 **Redis**: ניהול session ותור עבודות
- 🌐 **עברית מלאה**: תמיכה מלאה ב-RTL

---

## 📋 דרישות מערכת

### Python
- **Python 3.9+** (מומלץ 3.11+)
- **לא תומך ב-Python 3.7** (google-generativeai דורש 3.9+)
- pip (מנהל חבילות)

### שירותים חיצוניים
- **Redis** (לניהול session ותור)
- **Telegram Bot Token** (מ-@BotFather)
- **Google Gemini API Key** (חינמי!)

---

## 🚀 התקנה והרצה

### 1️⃣ Clone הפרויקט
```bash
cd c:\Dev\telegram-mcq-bot-python
```

### 2️⃣ הגדר Redis

#### אופציה א': Docker (מומלץ) ✅
```bash
docker run -d -p 6379:6379 --name telegram-bot-redis redis:alpine
```

#### אופציה ב': התקנה ידנית
- **Windows**: הורד מ-https://redis.io/download
- **Linux**: `sudo apt-get install redis-server && sudo service redis-server start`
- **Mac**: `brew install redis && brew services start redis`

בדוק ש-Redis רץ:
```bash
redis-cli ping
# צריך להחזיר: PONG
```

### 3️⃣ קבל API Keys

#### 🔑 Telegram Bot Token
1. פתח Telegram
2. חפש `@BotFather`
3. שלח `/newbot`
4. עקוב אחרי ההוראות
5. שמור את ה-TOKEN

#### 🔑 Google Gemini API Key (חינמי!)
1. כנס ל: https://makersuite.google.com/app/apikey
2. לחץ "Create API key"
3. שמור את המפתח

**מודלים נתמכים (נכון לנובמבר 2024):**
- `gemini-2.0-flash` - מהיר וחינמי (מומלץ!)
- `gemini-2.0-flash-001` - גרסה ספציפית
- `gemini-2.5-flash` - חדש יותר
- `gemini-pro-latest` - גרסה כללית

**הערה:** `gemini-pro` הישן כבר לא נתמך! השתמש ב-`gemini-2.0-flash`

### 4️⃣ הגדר .env

צור קובץ `.env` (העתק מ-`.env.example`):

```env
# Telegram Bot (חובה)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Google Gemini (חובה)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-pro

# Redis (אופציונלי - defaults)
REDIS_HOST=localhost
REDIS_PORT=6379

# הגדרות מערכת (אופציונלי)
MAX_FILE_SIZE_MB=15
MAX_QUESTIONS=50
RATE_LIMIT_PER_10MIN=5
RATE_LIMIT_PER_DAY=50
LOG_LEVEL=INFO
```

### 5️⃣ הרץ את השירות!

#### 🌐 אופציה א': ממשק אינטרנטי + בוט טלגרם (מומלץ!)
```bash
# Windows
start_web.bat

# Linux/Mac  
bash start_web.sh
```

#### 📱 אופציה ב': רק ממשק אינטרנטי
```bash
# Windows (בלי בוט טלגרם, למניעת conflicts)
start_web_only.bat
```

#### 🤖 אופציה ג': רק בוט טלגרם (כמו קודם)
```bash
# Windows:
start.bat

# Linux/Mac:
chmod +x start.sh
./start.sh
```

**🌐 גישה לממשק האינטרנטי**: http://localhost:10000

#### אופציה ב': ידני
```bash
# צור virtual environment עם Python 3.11
py -3.11 -m venv venv
# או
python3.11 -m venv venv
# או (אם Python 3.11 הוא ברירת המחדל)
python -m venv venv

# הפעל (Windows Git Bash)
source venv/Scripts/activate

# הפעל (Windows CMD)
venv\Scripts\activate.bat

# הפעל (Linux/Mac)
source venv/bin/activate

# התקן תלויות
pip install -r requirements.txt

# הגדר PYTHONPATH והרץ
export PYTHONPATH=$(pwd)  # Git Bash/Linux/Mac
# או
set PYTHONPATH=%CD%       # Windows CMD

python src/main.py
```

צריך לראות:
```
[INFO] Using Google Gemini (gemini-pro)
[INFO] Connected to Redis at localhost:6379
[INFO] Starting background workers...
[INFO] 🚀 Telegram MCQ Bot is running!
```

---

## 🎯 שימוש במערכת

### 🌐 **ממשק אינטרנטי (חדש!)**

1. **פתח דפדפן** על http://localhost:10000
2. **לחץ "התחל עכשיו"** או "יצירת מבחן חדש"  
3. **העלה קובץ/קבצים** (PDF, DOCX, TXT עד 15MB)
4. **בחר מספר שאלות** (3-50, המערכת ממליצה על סמך אורך הטקסט)
5. **קבל מבחן מוכן** עם אפשרויות הורדה והדפסה

### 📱 **בוט טלגרם**

### 1. פתח את הבוט בטלגרם
חפש את הבוט שיצרת (השם שנתת ל-@BotFather)

### 2. שלח `/start`
תקבל הודעת ברוכים הבאים

### 3. העלה קובץ
שלח קובץ PDF, DOCX או TXT (עד 15MB)

### 4. קבל המלצה
הבוט יגיד כמה מילים מצא ויציע מספר שאלות

### 5. בחר כמות
שלח מספר בין 3-50

### 6. קבל מבחן!
תוך 10-60 שניות תקבל קובץ HTML מוכן

### 7. פתח בדפדפן
פתח את הקובץ ב-Chrome/Firefox/Safari ותענה על השאלות! 🎉

---

## 📦 מבנה הפרויקט

```
telegram-mcq-bot-python/
├── src/
│   ├── main.py                    # Entry point
│   ├── config.py                  # Configuration
│   │
│   ├── handlers/
│   │   ├── start.py              # /start command
│   │   ├── document.py           # File upload
│   │   └── text.py               # Question count input
│   │
│   ├── services/
│   │   ├── file_service.py       # PDF/DOCX/TXT processing
│   │   ├── generator_service.py  # Gemini question generation
│   │   ├── html_renderer.py      # HTML quiz creation
│   │   ├── session_service.py    # Redis sessions
│   │   └── queue_service.py      # Background jobs
│   │
│   └── utils/
│       ├── logger.py             # Logging
│       └── validators.py         # Input validation
│
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
├── .env                          # Your config (don't commit!)
├── .gitignore
├── start.sh                      # Quick start (Linux/Mac)
├── start.bat                     # Quick start (Windows)
└── README.md
```

---

## 🔧 פתרון בעיות

### "Configuration errors: TELEGRAM_BOT_TOKEN is required"
❌ **בעיה**: חסר Telegram Bot Token

✅ **פתרון**:
1. בדוק שיש לך קובץ `.env`
2. הוסף את ה-TOKEN מ-@BotFather
3. ודא שהשורה לא מתחילה ב-`#`

### "Failed to connect to Redis"
❌ **בעיה**: Redis לא רץ

✅ **פתרון**:
```bash
# Docker:
docker start telegram-bot-redis

# Local:
# Windows: הפעל את redis-server.exe
# Linux: sudo service redis-server start
# Mac: brew services start redis

# בדוק:
redis-cli ping
```

### "Import 'telegram' could not be resolved"
❌ **בעיה**: חבילות לא מותקנות

✅ **פתרון**:
```bash
# ודא שה-venv פעיל
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# התקן מחדש:
pip install -r requirements.txt
```

### הבוט לא מגיב בטלגרם
❌ **בעיה**: הבוט לא רץ או Token שגוי

✅ **פתרון**:
1. בדוק שהטרמינל מראה "Bot is running"
2. נסה Token חדש מ-@BotFather
3. בדוק שאין instance אחר שרץ:
```bash
# Windows:
tasklist | findstr python
# Linux/Mac:
ps aux | grep python
```

### "BlockedPromptException" מ-Gemini
❌ **בעיה**: Gemini חסם את הטקסט

✅ **פתרון**:
- נסה טקסט אחר (פחות "רגיש")
- בדוק שה-API key תקין
- חכה כמה דקות (אולי הגעת ל-quota)

---

## 💡 טיפים

### שיפור איכות השאלות
- השתמש בטקסט מובנה ומסודר
- לפחות 500 מילים לתוצאות טובות
- טקסט עם מידע עובדתי (לא סיפורי)

### ביצועים
- קבצים קטנים (< 5MB) → עיבוד מהיר יותר
- פחות שאלות → תוצאות מהירות יותר
- Gemini לפעמים איטי - סבלנות 🙏

### אבטחה
- **לעולם אל תשתף את ה-.env**
- גיבוי של API keys במקום בטוח
- בדוק את `logs/` לבעיות

---

## 📊 מגבלות

### מוכללות
- גודל קובץ: **15MB מקסימום**
- מספר שאלות: **3-50**
- Rate limit: **5 בקשות / 10 דקות, 50 בקשות / יום**

### Gemini API (Free Tier)
- ✅ 60 requests / דקה
- ✅ 1,500 requests / יום
- ✅ מספיק למאות משתמשים

### Redis
- תלות בזמינות Redis
- Session TTL: 15 דקות
- File data TTL: 72 שעות

---

## 🎓 אדריכלות

```
User → Telegram → Bot Handler
                    ↓
              Session Service (Redis)
                    ↓
              File Service (Extract Text)
                    ↓
              Queue Service (Add Job)
                    ↓
         Background Worker (3 workers)
                    ↓
         Generator Service (Gemini AI)
                    ↓
         HTML Renderer (Create Quiz)
                    ↓
         Send to User ← Bot Handler
```

---

## ☁️ פריסה בענן (Render)

רוצה להריץ את הבוט 24/7 בענן? יש לך 2 אפשרויות:

### אופציה 1: פריסה אוטומטית (הכי קל!)
1. Push את הקוד ל-GitHub
2. לך ל-[Render](https://render.com) → **New Blueprint**
3. בחר את הrepository → Render יזהה את `render.yaml`
4. הוסף משתני סביבה: `TELEGRAM_BOT_TOKEN` + `GEMINI_API_KEY`
5. לחץ **Apply** → תוך 5 דקות הבוט רץ! 🎉

### אופציה 2: פריסה ידנית
קרא את [DEPLOYMENT.md](./DEPLOYMENT.md) למדריך מפורט שלב-אחר-שלב.

### 💰 עלויות
- **Free Plan**: 750 שעות/חודש (מספיק לרוב המקרים!)
- **Redis Free**: 25MB RAM
- **חיסרון**: "cold start" אחרי 15 דקות חוסר פעילות

### ⏰ למנוע Cold Starts (אופציונלי)
הבוט נרדם אחרי 15 דקות חוסר פעילות ב-Free Plan.  
**פתרון:** השתמש ב-[UptimeRobot](https://uptimerobot.com) (חינמי!) שישלח ping כל 5 דקות.

📖 **מדריך מלא:** קרא את [KEEPALIVE.md](./KEEPALIVE.md)

---

## 🆘 תמיכה

### יש בעיה?
1. בדוק ב-**פתרון בעיות** למעלה
2. הסתכל ב-`logs/bot_YYYYMMDD.log`
3. הפעל עם `LOG_LEVEL=DEBUG` ב-.env

### רוצה לתרום?
Pull Requests מתקבלים בברכה! 🙌

---

## 📝 רישוי

MIT License - חופשי לשימוש מסחרי ופרטי

---

## 🙏 תודות

- **Google Gemini** - AI engine חינמי ומדהים
- **python-telegram-bot** - ספרייה מעולה
- **Redis** - מהיר וקל
- **כל המשתמשים שלנו** ❤️

---

## 📋 Checklist להרצה ראשונה

- [ ] Python 3.7.9+ מותקן (`python --version`)
- [ ] Redis רץ (`redis-cli ping` → PONG)
- [ ] יצרתי virtual environment
- [ ] התקנתי `pip install -r requirements.txt`
- [ ] יש לי Telegram Bot Token מ-@BotFather
- [ ] יש לי Gemini API Key מ-Google AI Studio
- [ ] יצרתי קובץ `.env` מ-`.env.example`
- [ ] מילאתי את TELEGRAM_BOT_TOKEN ב-.env
- [ ] מילאתי את GEMINI_API_KEY ב-.env
- [ ] הרצתי `python src/main.py` (או start.bat)
- [ ] הבוט מגיב ל-`/start` בטלגרם ✅

**אם הכל מסומן - מזל טוב! הבוט שלך רץ!** 🎉

---

**נוצר עם ❤️ על ידי GitHub Copilot**
