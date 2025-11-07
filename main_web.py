#!/usr/bin/env python3
"""
Telegram MCQ Bot - Web Service Entry Point
Entry point that runs both the Telegram bot and a simple HTTP health server
"""
import sys
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Import and run the main function from src/main.py
import main as src_main

class HealthHandler(BaseHTTPRequestHandler):
    """Simple HTTP health check handler"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/' or self.path == '/health':
            # Health check endpoint
            response = {
                'status': 'healthy',
                'service': 'telegram-mcq-bot',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'version': '1.0.0'
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        else:
            # 404 for other paths
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not Found'}).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def run_health_server():
    """Run HTTP health check server"""
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"🌐 Health server running on port {port}")
    server.serve_forever()

def main():
    """Main entry point that runs both bot and health server"""
    try:
        # Start health server in background thread
        health_thread = threading.Thread(target=run_health_server, daemon=True)
        health_thread.start()
        
        # Run the telegram bot (this will block)
        src_main.main()
        
    except Exception as e:
        print(f"Error starting services: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()