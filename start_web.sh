#!/bin/bash
# Start both Flask web app and Telegram bot

echo "🚀 Starting MCQ Bot Web Application..."

# Set Python path
export PYTHONPATH="$(pwd)/src"

# Check if Redis is running
redis-cli ping &>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Redis is running"
else
    echo "⚠️  Redis not found - sessions will use Flask session fallback"
fi

# Check .env file
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please create .env file from .env.example"
    exit 1
fi

echo "🌐 Starting Flask web interface..."
echo "📱 Telegram bot will start automatically"
echo ""
echo "Access the web interface at: http://localhost:10000"
echo "Press Ctrl+C to stop"
echo ""

# Run the hybrid application
python main_web.py