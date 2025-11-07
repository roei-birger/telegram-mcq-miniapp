#!/usr/bin/env python3
"""
Alternative entry point for deployment issues
Ensures templates are found by running from correct directory
"""
import os
import sys

def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to src directory
    src_dir = os.path.join(script_dir, 'src')
    if os.path.exists(src_dir):
        os.chdir(src_dir)
        print(f"Changed working directory to: {os.getcwd()}")
    
    # Add src to Python path
    sys.path.insert(0, src_dir)
    
    # Import and run the web app
    try:
        from web_app import app
        port = int(os.environ.get('PORT', 10000))
        print(f"Starting Flask app on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f"Error starting app: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()