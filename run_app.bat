@echo off
echo Installing dependencies...
py -3.11 -m pip install -r requirements.txt
echo Starting the application...
py -3.11 app.py
echo.
pause 