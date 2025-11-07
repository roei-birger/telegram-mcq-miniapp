#!/usr/bin/env python3
"""
Telegram MCQ Bot - Main Entry Point for Deployment
Entry point that properly sets up Python path and imports
"""
import sys
import os

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Import and run the main function from src/main.py
import main as src_main

if __name__ == "__main__":
    src_main.main()