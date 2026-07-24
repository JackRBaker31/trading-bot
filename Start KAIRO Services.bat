@echo off
setlocal

title KAIRO Services Launcher
color 0B

set "ROOT=C:\Users\Jack\Documents\trading-bot"

if not exist "%ROOT%\.venv\Scripts\python.exe" (
    color 0C
    echo ERROR: Python was not found:
    echo %ROOT%\.venv\Scripts\python.exe
    echo.
    pause
    exit /b 1
)

echo Starting KAIRO Job Worker in its own persistent window...
start "KAIRO Job Worker" cmd.exe /d /k "cd /d %ROOT% && .venv\Scripts\python.exe -m app.run_job_worker"

echo Starting KAIRO Scheduler in its own persistent window...
start "KAIRO Scheduler" cmd.exe /d /k "cd /d %ROOT% && .venv\Scripts\python.exe -m app.run_scheduler"

echo.
echo KAIRO background services have been launched independently.
echo Keep both windows open while KAIRO is running.
echo.
pause

endlocal
exit /b 0
