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

".venv\Scripts\python.exe" ".\run_kairo.py" --foreground

if errorlevel 1 (
    echo.
    echo KAIRO failed to start.
    pause
)

endlocal
exit /b %errorlevel%
