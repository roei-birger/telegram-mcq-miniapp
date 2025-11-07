#!/usr/bin/env bash
# Build script for Render

set -o errexit

echo "📦 Python version: $(python --version)"
echo "📍 Python path: $(which python)"

# Force Python 3.11 if available
if command -v python3.11 &> /dev/null; then
    echo "✅ Found Python 3.11, using it..."
    alias python=python3.11
    alias pip=pip3.11
fi

echo "🔧 Using: $(python --version)"

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs temp outputs

echo "✅ Build completed successfully!"
