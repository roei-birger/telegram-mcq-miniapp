# 🚀 פריסת הבוט ב-Render

מדריך שלב-אחר-שלב לפריסת Telegram MCQ Bot ב-Render.

---

## 📋 דרישות מוקדמות

1. **חשבון GitHub** - הקוד צריך להיות ב-repository
2. **חשבון Render** - הירשם ב-https://render.com (חינמי!)
3. **Telegram Bot Token** - מ-@BotFather
4. **Gemini API Key** - מ-https://makersuite.google.com/app/apikey

---

## 🔧 שלבי פריסה

### 1️⃣ הכנת הקוד

```bash
# וודא שכל השינויים נשמרו
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 2️⃣ יצירת Blueprint ב-Render

#### אופציה א': פריסה אוטומטית (מומלץ)

1. כנס ל-https://render.com
2. לחץ **New +** → **Blueprint**
3. התחבר ל-GitHub ובחר את הrepository
4. Render יזהה את `render.yaml` אוטומטית
5. לחץ **Apply**

#### אופציה ב': פריסה ידנית

**צעד 1: יצירת Redis Database**
1. לחץ **New +** → **Redis**
2. Name: `telegram-bot-redis`
3. Plan: **Free**
4. Region: בחר הקרוב אליך
5. לחץ **Create Redis**
6. שמור את **Internal Redis URL** (נדרש בהמשך)

**צעד 2: יצירת Web Service**
1. לחץ **New +** → **Web Service**
2. התחבר ל-GitHub repository
3. הגדרות:
   - **Name:** `telegram-mcq-bot`
   - **Runtime:** Python 3
   - **Build Command:** `bash build.sh`
   - **Start Command:** `python src/main.py`
   - **Plan:** Free

### 3️⃣ הגדרת משתני סביבה

ב-Dashboard של ה-Web Service, עבור ל-**Environment** והוסף:

```env
TELEGRAM_BOT_TOKEN=your_telegram_token_here
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-2.0-flash
REDIS_HOST=<Redis Internal Host>
REDIS_PORT=<Redis Port (6379)>
MAX_FILE_SIZE_MB=15
MAX_QUESTIONS=50
RATE_LIMIT_PER_10MIN=5
RATE_LIMIT_PER_DAY=50
LOG_LEVEL=INFO
PYTHONUNBUFFERED=1
```

**💡 טיפ:** אם השתמשת ב-Blueprint, רוב המשתנים כבר מוגדרים. תצטרך רק למלא:
- `TELEGRAM_BOT_TOKEN`
- `GEMINI_API_KEY`

### 4️⃣ פריסה

1. שמור את משתני הסביבה
2. Render יתחיל deploy אוטומטית
3. עקוב אחרי הlogs ב-**Logs** tab
4. המתן לסימן ירוק ✅

### 5️⃣ בדיקה

1. פתח את הבוט בטלגרם
2. שלח `/start`
3. העלה קובץ ונסה ליצור מבחן

---

## 📊 ניטור ותחזוקה

### צפייה ב-Logs
```
Dashboard → Your Service → Logs
```

### Restart השירות
```
Dashboard → Your Service → Manual Deploy → Deploy Latest Commit
```

### עדכון קוד
```bash
# בlocal
git add .
git commit -m "Your changes"
git push origin main

# Render יעשה deploy אוטומטית!
```

---

## 🔍 פתרון בעיות

### הבוט לא מגיב

**בדיקה 1:** Logs
```
Dashboard → Logs → חפש errors
```

**שגיאות נפוצות:**
- `Configuration errors: TELEGRAM_BOT_TOKEN is required` → הוסף את הToken במשתני סביבה
- `Failed to connect to Redis` → וודא ש-REDIS_HOST ו-REDIS_PORT נכונים
- `ModuleNotFoundError` → בדוק את build.sh שרץ בהצלחה

**בדיקה 2:** Redis רץ?
```
Dashboard → Redis Service → Status: Active
```

**בדיקה 3:** Environment Variables
```
Dashboard → Web Service → Environment → בדוק שכל המשתנים מוגדרים
```

### זמן אחזור איטי (Cold Start)

Render Free Plan עלול להכניס את השירות ל"שינה" אחרי 15 דקות חוסר פעילות.

**פתרון 1:** שדרג ל-Starter Plan ($7/חודש)

**פתרון 2:** השתמש ב-UptimeRobot
- https://uptimerobot.com
- צור monitor ש-pings את השירות כל 5 דקות
- **שים לב:** Render לא אוהב health checks ממש, אבל זה עוזר

**פתרון 3:** קבל health check endpoint (אופציונלי)
```python
# src/handlers/start.py - הוסף handler
@app.route('/health')
def health():
    return 'OK', 200
```

### הבוט עובד אבל לא יוצר שאלות

**בדיקה:** Gemini API
- לך ל-https://makersuite.google.com/app/apikey
- בדוק שה-API key תקף
- בדוק quota (60 requests/min, 1500/day)

---

## 💰 עלויות

### Free Plan (מספיק לבוט קטן-בינוני)
- **Web Service:** 750 hours/month חינם
- **Redis:** 25MB RAM חינם
- **חיסרון:** Cold starts אחרי 15 דקות

### Starter Plan ($7/month)
- **Web Service:** Always on, no cold starts
- **Redis:** 256MB RAM
- מומלץ אם יש לך הרבה משתמשים

---

## 🔐 אבטחה

### המלצות:
1. **אל תשמור secrets בקוד** - השתמש במשתני סביבה בלבד
2. **הגבל גישה ל-Redis** - השאר `ipAllowList: []` ב-render.yaml
3. **Rate Limiting** - כבר מוגדר בקוד (5 בקשות/10 דקות)
4. **גיבוי Tokens** - שמור את הBot Token ו-API keys במקום בטוח

---

## 🆘 צריך עזרה?

1. **Render Docs:** https://render.com/docs
2. **Telegram Bot API:** https://core.telegram.org/bots/api
3. **Gemini API:** https://ai.google.dev/docs

---

## ✅ Checklist

- [ ] קוד ב-GitHub repository
- [ ] יצרתי חשבון Render
- [ ] יש לי Telegram Bot Token
- [ ] יש לי Gemini API Key
- [ ] יצרתי Redis service ב-Render
- [ ] יצרתי Web Service ב-Render
- [ ] הגדרתי את כל משתני הסביבה
- [ ] הבוט deployed בהצלחה (✅ בlogs)
- [ ] הבוט עונה ל-/start בטלגרם
- [ ] הבוט יוצר מבחנים בהצלחה

**אם הכל מסומן - מזל טוב! הבוט שלך רץ בענן! 🎉**

---

**נוצר עם ❤️ על ידי GitHub Copilot**
