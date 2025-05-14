@echo off
echo Installing dependencies...
py -3.11 -m pip install flask flask-sqlalchemy werkzeug

echo Starting Simple Fashion Store E-commerce Website...
echo.
py -3.11 simple_app.py
pause 