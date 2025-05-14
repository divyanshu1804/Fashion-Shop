@echo off
echo Installing dependencies...
py -3.11 -m pip install flask flask-sqlalchemy werkzeug

echo Removing old database...
if exist instance\ecommerce.db del /f instance\ecommerce.db

echo Starting Basic Fashion Store E-commerce Website...
echo.
py -3.11 basic_app.py
pause 