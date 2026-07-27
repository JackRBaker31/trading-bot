@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo KAIRO virtual environment was not found.
    echo Expected:
    echo %CD%\.venv\Scripts\python.exe
    echo.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" ".\run_kairo.py" ^
    --foreground ^
    --monitor ^
    --monitor-interval 10 ^
    --restart-delay 5 ^
    --restart-window 300 ^
    --max-restarts 5

if errorlevel 1 (
    echo.
    echo KAIRO worker watchdog stopped after repeated failures.
    echo Review:
    echo data\runtime\launcher-events.jsonl
    echo.
    pause
)

endlocal
exit /b %errorlevel%
