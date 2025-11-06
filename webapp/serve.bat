@echo off
REM Simple HTTP Server for testing Mini App

echo Starting HTTP server on port 8000...
echo.
echo Mini App URL: http://localhost:8000/miniapp.html
echo.
echo Press Ctrl+C to stop
echo.

cd webapp
python -m http.server 8000
