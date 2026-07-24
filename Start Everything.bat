@echo off
setlocal

title KAIRO Master Launcher
color 0B

set "ROOT=C:\Users\Jack\Documents\trading-bot"

echo ============================================================
echo              STARTING THE KAIRO PLATFORM
echo ============================================================
echo.

echo Launching API + Frontend...
start "" "%ROOT%\Start KAIRO.bat"

timeout /t 2 /nobreak >nul

echo Launching Worker + Scheduler...
start "" "%ROOT%\Start KAIRO Services.bat"

echo.
echo ============================================================
echo KAIRO launch initiated.
echo.
echo Four windows should open:
echo.
echo   - KAIRO API
echo   - KAIRO Frontend
echo   - KAIRO Job Worker
echo   - KAIRO Scheduler
echo ============================================================
echo.

exit