@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" ".\run_kairo.py" --status
echo.
pause
endlocal
exit /b 0
