#!/bin/bash
# Quick start script for Linux/Mac

echo "🚀 Starting Telegram MCQ Bot..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "✨ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check .env file
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Please create .env file from .env.example"
    exit 1
fi

# Start bot
echo "🤖 Starting bot..."
export PYTHONPATH=$(pwd)
python main.py
