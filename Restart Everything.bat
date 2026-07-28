@echo off
setlocal
cd /d "%~dp0"

title Restart KAIRO Unified Platform Supervisor
color 0B

".venv\Scripts\python.exe" ".\run_kairo.py" ^
    --restart ^
    --foreground ^
    --monitor ^
    --monitor-interval 10 ^
    --restart-delay 5 ^
    --restart-window 300 ^
    --max-restarts 5

if errorlevel 1 (
    color 0C
    echo.
    echo KAIRO restart failed.
    echo Review data\runtime\launcher-events.jsonl
    pause
)

endlocal
exit /b %errorlevel%
