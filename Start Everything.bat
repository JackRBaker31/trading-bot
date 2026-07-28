@echo off
setlocal
cd /d "%~dp0"

title KAIRO Unified Platform Supervisor
color 0B

if not exist ".venv\Scripts\python.exe" (
    color 0C
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
    color 0C
    echo.
    echo KAIRO Platform Supervisor stopped after a failure.
    echo Review:
    echo data\runtime\launcher-events.jsonl
    echo data\supervisor_status.json
    echo.
    pause
)

endlocal
exit /b %errorlevel%
