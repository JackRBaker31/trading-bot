@echo off
setlocal EnableExtensions EnableDelayedExpansion

title KAIRO Full Test Suite
color 0B

set "ROOT=C:\Users\Jack\Documents\trading-bot"
set "PYTHON=%ROOT%\.venv\Scripts\python.exe"
set "FRONTEND=%ROOT%\frontend"
set "FAILED=0"

cls
echo ============================================================
echo                   KAIRO TEST SUITE
echo ============================================================
echo.

if not exist "%PYTHON%" (
    color 0C
    echo [ERROR] Virtual environment Python not found:
    echo         %PYTHON%
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

echo ------------------------------------------------------------
echo [1/4] Backend tests
echo ------------------------------------------------------------
"%PYTHON%" -m pytest -q
if errorlevel 1 (
    echo.
    echo Backend tests............. FAILED
    set "FAILED=1"
) else (
    echo.
    echo Backend tests............. PASSED
)

echo.
echo ------------------------------------------------------------
echo [2/4] Frontend TypeScript
echo ------------------------------------------------------------
cd /d "%FRONTEND%"
call npm.cmd run typecheck
if errorlevel 1 (
    echo.
    echo TypeScript................ FAILED
    set "FAILED=1"
) else (
    echo.
    echo TypeScript................ PASSED
)

echo.
echo ------------------------------------------------------------
echo [3/4] Frontend tests
echo ------------------------------------------------------------
call npm.cmd run test
if errorlevel 1 (
    echo.
    echo Frontend tests............ FAILED
    set "FAILED=1"
) else (
    echo.
    echo Frontend tests............ PASSED
)

echo.
echo ------------------------------------------------------------
echo [4/4] Production build
echo ------------------------------------------------------------
call npm.cmd run build
if errorlevel 1 (
    echo.
    echo Production build.......... FAILED
    set "FAILED=1"
) else (
    echo.
    echo Production build.......... PASSED
)

echo.
echo ============================================================

if "%FAILED%"=="0" (
    color 0A
    echo                  ALL SYSTEMS GREEN
    echo ============================================================
    echo.
    echo Backend tests............. PASSED
    echo TypeScript................ PASSED
    echo Frontend tests............ PASSED
    echo Production build.......... PASSED
    echo.
    pause
    exit /b 0
)

color 0C
echo                  TEST SUITE FAILED
echo ============================================================
echo.
echo One or more validation stages failed.
echo Review the output above.
echo.
pause
exit /b 1
