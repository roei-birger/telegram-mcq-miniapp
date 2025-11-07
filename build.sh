#!/usr/bin/env bash
# Build script for Render

set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs temp outputs

echo "✅ Build completed successfully!"
