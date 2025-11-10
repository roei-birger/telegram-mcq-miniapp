#!/usr/bin/env bash
# Build script for Render

set -o errexit

echo "📦 Python version: $(python --version)"

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs temp outputs

# CRITICAL: Ensure templates and static are available at root level for deployment
echo "📁 Setting up templates and static files for Render deployment..."
echo "   Working directory: $(pwd)"
echo "   Directory contents before copy:"
ls -la

# First, check if we have templates in src
if [ -d "src/templates" ]; then
    echo "   ✅ Found src/templates directory"
    echo "   📄 Source template files:"
    ls -la src/templates/
    
    # Remove existing root templates if they exist
    if [ -d "templates" ]; then
        echo "   🗑️  Removing existing root templates directory"
        rm -rf templates
    fi
    
    # Copy templates to root
    echo "   📁 Copying templates: src/templates → ./templates"
    cp -r src/templates ./templates
    
    # Verify templates were copied correctly
    if [ -d "templates" ]; then
        echo "   ✅ Templates directory created at root"
        echo "   📄 Root template files:"
        ls -la templates/
        
        # Check for critical templates
        critical_templates=("index.html" "upload.html" "questions.html" "quiz.html" "error.html")
        for template in "${critical_templates[@]}"; do
            if [ -f "templates/$template" ]; then
                echo "   ✅ $template exists"
            else
                echo "   ❌ $template MISSING!"
            fi
        done
    else
        echo "   ❌ FAILED to create templates directory at root!"
        exit 1
    fi
else
    echo "   ❌ src/templates directory not found!"
    echo "   📁 Available directories in src/:"
    if [ -d "src" ]; then
        ls -la src/
    else
        echo "   ❌ src directory not found at all!"
        ls -la
    fi
    exit 1
fi

# Copy static files
if [ -d "src/static" ]; then
    echo "   ✅ Found src/static directory"
    
    # Remove existing root static if it exists
    if [ -d "static" ]; then
        echo "   🗑️  Removing existing root static directory"
        rm -rf static
    fi
    
    echo "   📁 Copying static files: src/static → ./static"
    cp -r src/static ./static
    
    if [ -d "static" ]; then
        echo "   ✅ Static files copied successfully"
    else
        echo "   ❌ Failed to copy static files"
    fi
else
    echo "   ⚠️  src/static directory not found!"
fi

# Final verification
echo "   � Final root directory contents:"
ls -la

echo "✅ Build completed successfully!"
