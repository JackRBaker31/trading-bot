@echo off
setlocal

title Restart KAIRO
color 0B

set "ROOT=C:\Users\Jack\Documents\trading-bot"

cls
echo ============================================================
echo                    RESTARTING KAIRO
echo ============================================================
echo.

call "%ROOT%\Stop KAIRO.bat"

echo.
echo Waiting for shutdown to complete...
timeout /t 3 >nul

call "%ROOT%\Start KAIRO.bat"

exit /b %ERRORLEVEL%
