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
echo "   Working directory: $(pwd)"
echo "   Directory contents before copy:"
ls -la

# Copy templates from src to root (critical for template path detection)
if [ -d "src/templates" ]; then
    echo "   ✅ Found src/templates directory"
    if [ ! -d "templates" ]; then
        echo "   📁 Copying templates: src/templates → ./templates"
        cp -r src/templates ./templates
        echo "   ✅ Templates copied successfully"
    else
        echo "   ℹ️  Root templates directory already exists, removing and re-copying"
        rm -rf templates
        cp -r src/templates ./templates
        echo "   ✅ Templates re-copied successfully"
    fi
    
    # Verify templates were copied
    if [ -d "templates" ]; then
        echo "   ✅ Templates directory exists at root"
        echo "   📄 Template files:"
        ls -la templates/
    else
        echo "   ❌ Failed to create templates directory!"
    fi
else
    echo "   ⚠️  src/templates directory not found!"
    echo "   📁 Available directories in src/:"
    ls -la src/
fi

# Copy static files from src to root  
if [ -d "src/static" ]; then
    echo "   ✅ Found src/static directory"
    if [ ! -d "static" ]; then
        echo "   📁 Copying static files: src/static → ./static"
        cp -r src/static ./static
        echo "   ✅ Static files copied successfully"
    else
        echo "   ℹ️  Root static directory already exists, skipping"
    fi
else
    echo "   ⚠️  src/static directory not found!"
fi

echo "   📁 Final directory contents:"
ls -la

# Verify the setup
echo "📋 Directory structure:"
ls -la
if [ -d "templates" ]; then
    echo "  Templates directory contents:"
    ls -la templates/
fi

echo "✅ Build completed successfully!"
