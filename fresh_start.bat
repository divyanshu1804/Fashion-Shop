@echo off
echo Stopping all running Flask servers...
taskkill /f /im python.exe /fi "WINDOWTITLE eq Python"

echo Installing dependencies...
py -3.11 -m pip install flask flask-sqlalchemy werkzeug

echo Removing old database...
if exist instance\ecommerce.db (
    taskkill /f /im python.exe
    timeout /t 2
    del /f instance\ecommerce.db
)

echo Starting Basic Fashion Store E-commerce Website...
echo.
py -3.11 basic_app.py
pause 