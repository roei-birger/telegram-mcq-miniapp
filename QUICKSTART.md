# 🚀 התקנה והרצה מהירה

## צעדים:

### 1. הכן את Redis
```bash
# Docker (מומלץ):
docker run -d -p 6379:6379 --name telegram-bot-redis redis:alpine

# או התקן local
```

### 2. הכן API Keys

**Telegram:**
- פתח @BotFather בטלגרם
- `/newbot` → עקוב אחרי ההוראות
- שמור את ה-TOKEN

**Gemini:**
- https://makersuite.google.com/app/apikey
- צור API key
- שמור אותו

### 3. הגדר .env
```bash
# העתק את .env.example ל-.env
cp .env.example .env

# ערוך ומלא:
TELEGRAM_BOT_TOKEN=your_token_here
GEMINI_API_KEY=your_key_here
```

### 4. הרץ!

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

### 5. בדוק
- פתח את הבוט בטלגרם
- שלח `/start`
- אם הבוט מגיב - מזל טוב! 🎉

---

## בעיות נפוצות

### Redis לא רץ
```bash
redis-cli ping
# צריך: PONG
```

### חבילות לא מותקנות
```bash
pip install -r requirements.txt
```

### הבוט לא מגיב
- בדוק שהטרמינל מראה "Bot is running"
- בדוק Token ב-.env
- נסה Token חדש

---

**מוכן לשימוש!** 🚀
