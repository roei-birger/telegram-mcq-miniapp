# ⏰ שמירה על הבוט ער (Prevent Cold Starts)

Render Free Plan מכניס שירותים ל"שינה" אחרי 15 דקות חוסר פעילות.  
כדי למנוע זאת, אפשר להשתמש בשירותי monitoring שישלחו ping לבוט כל כמה דקות.

---

## 🎯 פתרונות מומלצים

**עדכון חשוב:** הבוט עכשיו כולל שרת HTTP פנימי לhealth checks!

### URL לניטור:
```
https://[YOUR-BOT-NAME].onrender.com/health
```

### תגובה צפויה:
```json
{
  "status": "healthy",
  "service": "telegram-mcq-bot", 
  "timestamp": "2025-11-07T19:32:00Z",
  "version": "1.0.0"
}
```

### אפשרות 1: UptimeRobot (הכי פופולרי!)

**יתרונות:**
- ✅ חינמי לחלוטין
- ✅ 50 monitors
- ✅ Ping כל 5 דקות
- ✅ התראות אם הבוט נופל

**הגדרה:**

1. **הירשם:** https://uptimerobot.com

2. **צור Monitor חדש:**
   - **Monitor Type:** HTTP(s)
   - **Friendly Name:** Telegram MCQ Bot
   - **URL:** `https://[YOUR-BOT-NAME].onrender.com` (הURL שRender נותן לך)
   - **Monitoring Interval:** 5 minutes
   - **Monitor Timeout:** 30 seconds

3. **שמור** → הבוט ישאר ער 24/7!

**💡 טיפ:** אם רוצה לבדוק ידנית, שלח `/health` לבוט בטלגרם

---

### אפשרות 2: Cron-job.org

**יתרונות:**
- ✅ חינמי
- ✅ Ping כל דקה (!)
- ✅ לא דורש הרשמה מייל

**הגדרה:**

1. **כנס ל:** https://cron-job.org

2. **צור Cronjob:**
   - **Title:** Keep Bot Alive
   - **URL:** `https://[YOUR-BOT-NAME].onrender.com`
   - **Schedule:** Every 5 minutes (*/5 * * * *)
   - **Enabled:** ✅

3. **שמור** → הבוט ישאר ער!

---

### אפשרות 3: Render Scheduled Job (פנימי)

Render מאפשר ליצור **Cron Job** ששולח request לבוט שלך.

**יצירה:**

1. ב-Render Dashboard → **New +** → **Cron Job**

2. **הגדרות:**
   - **Name:** keep-bot-alive
   - **Runtime:** Shell
   - **Schedule:** `*/5 * * * *` (כל 5 דקות)
   - **Command:**
     ```bash
     curl -s https://[YOUR-BOT-NAME].onrender.com || echo "Health check"
     ```

3. **Create** → זה ירוץ אוטומטית!

**⚠️ חיסרון:** Cron Jobs ב-Render לא חינמיים לחלוטין (עשויים לחייב אחרי זמן מה)

---

## 🔍 איך לבדוק שזה עובד?

### בדיקה 1: Logs ב-Render
```
Dashboard → Your Service → Logs
```
תראה:
```
[INFO] Health check from chat_id=...
```

### בדיקה 2: בטלגרם
שלח `/health` לבוט → תקבל:
```
✅ Bot is healthy
⏰ 2025-11-07 15:30:45
```

### בדיקה 3: UptimeRobot Dashboard
אם הגדרת UptimeRobot, תראה "Up" בירוק.

---

## 📊 השוואה מהירה

| שירות | חינמי | תדירות | קל להגדרה | התראות |
|-------|-------|---------|------------|---------|
| **UptimeRobot** | ✅ | כל 5 דקות | ⭐⭐⭐ | ✅ |
| **Cron-job.org** | ✅ | כל דקה | ⭐⭐⭐ | ✅ |
| **Render Cron** | ⚠️ (מוגבל) | כל 5 דקות | ⭐⭐ | ❌ |

**המלצה:** **UptimeRobot** - הכי מאוזן!

---

## 🔒 אבטחה

**שים לב:** כל שירות external יכול לגשת לURL שלך.

**מה הבוט עושה בפינג:**
- `/health` מחזיר רק "Bot is healthy" + timestamp
- לא חושף מידע רגיש
- לא מאפשר פעולות מנהליות

**אם רוצה אבטחה יותר חזקה:**
הוסף secret token ב-URL:
```python
# src/handlers/health.py
def health_check(update: Update, context: CallbackContext) -> None:
    # קבל ?token=... מההודעה
    # השווה ל-environment variable
    pass
```

---

## 💰 למה לא לשדרג ל-Starter Plan?

**Starter Plan ($7/חודש):**
- ✅ אין cold starts בכלל
- ✅ יותר CPU ו-RAM
- ✅ לא צריך keepalive hacks

**כדאי אם:**
- יש לך הרבה משתמשים (>100/יום)
- רוצה מהירות מקסימלית
- לא רוצה להסתבך עם monitoring

---

## ✅ Checklist

- [ ] הוספתי `/health` command לבוט (כבר עשינו!)
- [ ] נרשמתי ל-UptimeRobot (או Cron-job.org)
- [ ] יצרתי Monitor עם URL של הבוט ב-Render
- [ ] הגדרתי interval ל-5 דקות
- [ ] בדקתי שהבוט עונה ל-`/health`
- [ ] בדקתי ב-Logs שהפינגים מגיעים

**אם הכל מסומן - הבוט שלך לא ייכנס לשינה! 🎉**

---

**טיפ אחרון:** אם משתמש שולח הודעה לבוט - זה גם מעיר אותו. רק אם **אף אחד לא משתמש** במשך 15 דקות הוא נרדם.
