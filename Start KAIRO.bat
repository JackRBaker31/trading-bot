@echo off
setlocal

title KAIRO Launcher
color 0B

set "ROOT=C:\Users\Jack\Documents\trading-bot"
set "PYTHON=%ROOT%\.venv\Scripts\python.exe"
set "FRONTEND=%ROOT%\frontend"

cls
echo ============================================================
echo                    KAIRO AI PLATFORM
echo ============================================================
echo.

if not exist "%PYTHON%" (
    color 0C
    echo ERROR: Python was not found:
    echo %PYTHON%
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

echo Starting backend...
start "KAIRO Backend Supervisor" cmd /k "title KAIRO Backend Supervisor && cd /d "%ROOT%" && "%PYTHON%" -m app.run_process_supervisor"

timeout /t 2 >nul

echo Starting frontend...
start "KAIRO Frontend" cmd /k "title KAIRO Frontend && cd /d "%FRONTEND%" && call npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort"

echo.
echo Waiting 8 seconds for startup...
timeout /t 8 >nul

echo.
echo Opening KAIRO...
start "" "http://127.0.0.1:5173"

echo.
echo Startup commands completed.
echo Review the Backend and Frontend windows if the site does not load.
echo.
pause

exit /b 0
