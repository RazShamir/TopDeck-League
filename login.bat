@echo off
REM Quick Google OAuth login to get SACSID

cd /d "%~dp0"

REM Use venv Python if available
if exist "venv\Scripts\python.exe" (
    set PYTHON=venv\Scripts\python.exe
) else (
    set PYTHON=python
)

echo Running Google OAuth login...
%PYTHON% google_login.py
pause
