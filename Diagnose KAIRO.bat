@echo off
setlocal

title KAIRO Launcher Diagnostic
color 0E

echo ============================================================
echo                KAIRO LAUNCHER DIAGNOSTIC
echo ============================================================
echo.

echo Project root:
if exist "C:\Users\Jack\Documents\trading-bot" (
    echo PASS
) else (
    echo FAIL
)

echo.
echo Python:
if exist "C:\Users\Jack\Documents\trading-bot\.venv\Scripts\python.exe" (
    echo PASS
    "C:\Users\Jack\Documents\trading-bot\.venv\Scripts\python.exe" --version
) else (
    echo FAIL
)

echo.
echo npm:
where npm.cmd
if errorlevel 1 (
    echo FAIL
) else (
    echo PASS
)

echo.
echo Port 8000:
netstat -ano | findstr ":8000"

echo.
echo Port 5173:
netstat -ano | findstr ":5173"

echo.
pause
