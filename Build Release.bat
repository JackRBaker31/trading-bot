@echo off
setlocal EnableExtensions

title Build KAIRO Release
color 0B

set "ROOT=C:\Users\Jack\Documents\trading-bot"
set "FRONTEND=%ROOT%\frontend"
set "RELEASE_ROOT=%ROOT%\release"
set "RELEASE_DIR=%RELEASE_ROOT%\KAIRO"
set "ZIP_PATH=%RELEASE_ROOT%\KAIRO-release.zip"

cls
echo ============================================================
echo                    BUILD KAIRO RELEASE
echo ============================================================
echo.

call "%ROOT%\Run Tests.bat"
if errorlevel 1 (
    color 0C
    echo.
    echo [ERROR] Release cancelled because validation failed.
    echo.
    pause
    exit /b 1
)

if exist "%RELEASE_DIR%" rmdir /s /q "%RELEASE_DIR%"
mkdir "%RELEASE_DIR%"
mkdir "%RELEASE_DIR%\frontend"

robocopy "%ROOT%\app" "%RELEASE_DIR%\app" /E /NFL /NDL /NJH /NJS >nul
if errorlevel 8 goto :failed

robocopy "%ROOT%\web" "%RELEASE_DIR%\web" /E /NFL /NDL /NJH /NJS >nul
if errorlevel 8 goto :failed

robocopy "%FRONTEND%\dist" "%RELEASE_DIR%\frontend\dist" /E /NFL /NDL /NJH /NJS >nul
if errorlevel 8 goto :failed

if exist "%ROOT%\requirements.txt" copy /y "%ROOT%\requirements.txt" "%RELEASE_DIR%\" >nul
if exist "%ROOT%\config.json" copy /y "%ROOT%\config.json" "%RELEASE_DIR%\config.example.json" >nul

if exist "%ZIP_PATH%" del /q "%ZIP_PATH%"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Compress-Archive -Path '%RELEASE_DIR%\*' -DestinationPath '%ZIP_PATH%' -Force"

if errorlevel 1 goto :failed

color 0A
echo.
echo ============================================================
echo                  RELEASE BUILD COMPLETE
echo ============================================================
echo.
echo %ZIP_PATH%
echo.
pause
exit /b 0

:failed
color 0C
echo.
echo ============================================================
echo                   RELEASE BUILD FAILED
echo ============================================================
echo.
pause
exit /b 1
