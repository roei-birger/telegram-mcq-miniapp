#!/usr/bin/env bash
# Build script for Render

set -o errexit

echo "📦 Python version: $(python --version)"

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs temp outputs

# Ensure templates and static are available at root level for deployment
echo "📁 Setting up templates and static files..."
if [ -d "src/templates" ] && [ ! -d "templates" ]; then
    echo "  Copying templates from src/ to root level..."
    cp -r src/templates ./
fi

if [ -d "src/static" ] && [ ! -d "static" ]; then
    echo "  Copying static files from src/ to root level..."
    cp -r src/static ./
fi

# Verify the setup
echo "📋 Directory structure:"
ls -la
if [ -d "templates" ]; then
    echo "  Templates directory contents:"
    ls -la templates/
fi

echo "✅ Build completed successfully!"
