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
echo "📁 Setting up templates and static files for Render deployment..."

# Copy templates from src to root (critical for template path detection)
if [ -d "src/templates" ]; then
    if [ ! -d "templates" ]; then
        echo "  ✅ Copying templates: src/templates → ./templates"
        cp -r src/templates ./
    else
        echo "  ℹ️  Root templates directory already exists"
    fi
else
    echo "  ⚠️  src/templates not found!"
fi

# Copy static files from src to root  
if [ -d "src/static" ]; then
    if [ ! -d "static" ]; then
        echo "  ✅ Copying static files: src/static → ./static"
        cp -r src/static ./
    else
        echo "  ℹ️  Root static directory already exists"
    fi
else
    echo "  ⚠️  src/static not found!"
fi

# Verify the setup
echo "📋 Directory structure:"
ls -la
if [ -d "templates" ]; then
    echo "  Templates directory contents:"
    ls -la templates/
fi

echo "✅ Build completed successfully!"
