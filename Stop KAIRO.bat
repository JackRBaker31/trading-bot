@echo off
setlocal

title Stop KAIRO
color 0E

cls
echo ============================================================
echo                     STOPPING KAIRO
echo ============================================================
echo.

echo Closing KAIRO Backend Supervisor window...
taskkill /FI "WINDOWTITLE eq KAIRO Backend Supervisor*" /T /F >nul 2>&1

echo Closing KAIRO Frontend window...
taskkill /FI "WINDOWTITLE eq KAIRO Frontend*" /T /F >nul 2>&1

echo Clearing any remaining listeners on ports 8000 and 5173...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ports=@(8000,5173); foreach($port in $ports){$items=Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue; foreach($item in $items){Stop-Process -Id $item.OwningProcess -Force -ErrorAction SilentlyContinue}}"

echo.
echo KAIRO shutdown completed.
echo.
pause

exit /b 0
