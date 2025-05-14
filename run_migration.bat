@echo off
echo Running database migration...
python migrate_db.py
echo.
echo Migration completed. Press any key to exit.
pause > nul 