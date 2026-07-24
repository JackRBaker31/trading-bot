@echo off
setlocal

cd /d "%~dp0"

".venv\Scripts\python.exe" ".\run_kairo.py" --restart --foreground

if errorlevel 1 (
    echo.
    echo KAIRO restart failed.
    pause
)

endlocal
exit /b %errorlevel%
