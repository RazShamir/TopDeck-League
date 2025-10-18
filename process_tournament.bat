@echo off
REM Wrapper script to run tournament processor on Windows

cd /d "%~dp0"

REM Use venv Python if available, otherwise fall back to system Python
if exist "venv\Scripts\python.exe" (
    set PYTHON=venv\Scripts\python.exe
) else (
    set PYTHON=python
)

REM Run the tournament processor with all arguments passed through
%PYTHON% process_tournament_complete.py %*

REM Keep window open so user can see the output
pause
