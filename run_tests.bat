@echo off
REM Run automated tests for TopDeck API (Windows)

cd /d "%~dp0"

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Running automated tests...
echo.

python scripts\run_tests.py

pause
