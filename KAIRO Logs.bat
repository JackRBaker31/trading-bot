@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" ".\run_kairo.py" --logs --lines 50
echo.
pause
endlocal
exit /b 0
