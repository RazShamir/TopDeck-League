@echo off
REM Start the TopDeck League API server (Windows)

cd /d "%~dp0"

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start the server
echo Starting TopDeck League API...
echo Server will be available at: http://127.0.0.1:8000
echo API docs available at: http://127.0.0.1:8000/docs
echo.
echo Press CTRL+C to stop the server
echo.

uvicorn app:app --host 127.0.0.1 --port 8000 --reload
