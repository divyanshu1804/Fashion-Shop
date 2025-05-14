@echo off
echo Installing dependencies...
py -3.11 -m pip install flask flask-sqlalchemy werkzeug authlib requests waitress

echo Starting Fashion Store E-commerce Website...
echo.
py -3.11 app.py
pause 