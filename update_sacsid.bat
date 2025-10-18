@echo off
REM Update SACSID cookie on Windows

if "%1"=="" (
    echo Usage: update_sacsid.bat YOUR_SACSID_COOKIE
    echo.
    echo To get your SACSID:
    echo   1. Open https://mtgarena.appspot.com in Chrome
    echo   2. Press F12 -^> Application -^> Cookies
    echo   3. Find SACSID and copy its value
    echo   4. Run: update_sacsid.bat YOUR_SACSID_VALUE
    exit /b 1
)

echo {"sacsid": "%1"} > .sacsid.json
echo SACSID cookie updated successfully!
echo Saved to .sacsid.json
pause
