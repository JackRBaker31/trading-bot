@echo off
setlocal

title KAIRO Process Supervisor
cd /d "C:\Users\Jack\Documents\trading-bot"

set "PYTHON_EXE=C:\Users\Jack\Documents\trading-bot\.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo ERROR: Virtual environment Python was not found.
    echo Expected: %PYTHON_EXE%
    echo.
    pause
    exit /b 1
)

echo ========================================
echo       Starting KAIRO Supervised
echo ========================================
echo.
echo This window supervises:
echo   - FastAPI API
echo   - Job Worker
echo   - Scheduler
echo.
echo Paper trading remains controlled from KAIRO.
echo Press Ctrl+C in this window to stop all supervised processes.
echo.

"%PYTHON_EXE%" -m app.run_process_supervisor

set "EXIT_CODE=%ERRORLEVEL%"
echo.
echo KAIRO supervisor exited with code %EXIT_CODE%.
pause
exit /b %EXIT_CODE%
