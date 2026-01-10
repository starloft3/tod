@echo off
echo ============================================
echo   Tides of Darkness - Stopping Game
echo ============================================
echo.

echo Stopping Python backend...
taskkill /FI "WINDOWTITLE eq ToD Backend*" /T /F >nul 2>nul

echo Stopping Node frontend...
taskkill /FI "WINDOWTITLE eq ToD Frontend*" /T /F >nul 2>nul

:: Also kill any orphaned processes
taskkill /F /IM "node.exe" /FI "WINDOWTITLE eq ToD*" >nul 2>nul

echo.
echo Game servers stopped.
echo.
pause
