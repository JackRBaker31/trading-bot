@echo off
setlocal EnableExtensions

title Update KAIRO Dependencies
color 0B

set "ROOT=C:\Users\Jack\Documents\trading-bot"
set "PYTHON=%ROOT%\.venv\Scripts\python.exe"
set "FRONTEND=%ROOT%\frontend"

cls
echo ============================================================
echo                 UPDATE KAIRO DEPENDENCIES
echo ============================================================
echo.

if not exist "%PYTHON%" (
    color 0C
    echo [ERROR] Virtual environment Python not found.
    echo.
    pause
    exit /b 1
)

where npm.cmd >nul 2>&1
if errorlevel 1 (
    color 0C
    echo [ERROR] npm.cmd could not be found.
    echo.
    pause
    exit /b 1
)

cd /d "%ROOT%"

echo [1/3] Upgrading pip...
"%PYTHON%" -m pip install --upgrade pip
if errorlevel 1 goto :failed

echo.
echo [2/3] Installing Python dependencies...
if exist "%ROOT%\requirements.txt" (
    "%PYTHON%" -m pip install -r "%ROOT%\requirements.txt"
    if errorlevel 1 goto :failed
) else (
    echo requirements.txt not found - skipped.
)

echo.
echo [3/3] Installing frontend dependencies...
cd /d "%FRONTEND%"
call npm.cmd install
if errorlevel 1 goto :failed

color 0A
echo.
echo ============================================================
echo              DEPENDENCY UPDATE SUCCESSFUL
echo ============================================================
echo.
pause
exit /b 0

:failed
color 0C
echo.
echo ============================================================
echo               DEPENDENCY UPDATE FAILED
echo ============================================================
echo.
pause
exit /b 1
