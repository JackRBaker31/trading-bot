@echo off
setlocal

title KAIRO Launcher
color 0B

set "ROOT=C:\Users\Jack\Documents\trading-bot"
set "FRONTEND=%ROOT%\frontend"

cls
echo ============================================================
echo                    KAIRO AI PLATFORM
echo ============================================================
echo.

if not exist "%ROOT%\.venv\Scripts\python.exe" (
    color 0C
    echo ERROR: Python was not found:
    echo %ROOT%\.venv\Scripts\python.exe
    echo.
    pause
    exit /b 1
)

if not exist "%ROOT%\run_web.py" (
    color 0C
    echo ERROR: run_web.py was not found.
    echo.
    pause
    exit /b 1
)

if not exist "%FRONTEND%\package.json" (
    color 0C
    echo ERROR: Frontend package.json was not found.
    echo.
    pause
    exit /b 1
)

where npm.cmd >nul 2>&1
if errorlevel 1 (
    color 0C
    echo ERROR: npm.cmd was not found.
    echo.
    pause
    exit /b 1
)

echo Starting KAIRO API in its own persistent window...
start "KAIRO API" cmd.exe /d /k "cd /d %ROOT% && .venv\Scripts\python.exe run_web.py"

timeout /t 3 /nobreak >nul

echo Starting KAIRO frontend in its own persistent window...
start "KAIRO Frontend" cmd.exe /d /k "cd /d %FRONTEND% && call npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort"

echo.
echo Waiting 8 seconds for startup...
timeout /t 8 /nobreak >nul

echo Opening KAIRO...
start "" "http://127.0.0.1:5173"

echo.
echo API and frontend have been launched independently.
echo Run "Start KAIRO Services.bat" separately for the worker and scheduler.
echo Do not close the API, Frontend, Worker or Scheduler windows while testing.
echo.
pause

endlocal
exit /b 0
