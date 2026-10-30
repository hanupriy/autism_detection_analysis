@echo off
echo ===================================================
echo   Autism Prediction System - Starting Web Server
echo ===================================================
echo.
echo Installing required packages...
pip install flask pandas matplotlib reportlab werkzeug

echo.
echo Starting Flask server...
echo Opening browser...
start http://127.0.0.1:5000
echo.
python app.py
pause
