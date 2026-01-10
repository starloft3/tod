@echo off
echo ============================================
echo   Tides of Darkness - Starting Game
echo ============================================
echo.

:: Check for Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.9+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

:: Check for Node
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js not found in PATH
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

:: Get the directory where this script is located
cd /d "%~dp0"

echo Starting backend server...
start "ToD Backend" cmd /k "python -m uvicorn tod.api.main:app --host 0.0.0.0 --port 8000 --reload"

:: Wait a moment for backend to start
timeout /t 3 /nobreak >nul

echo Starting frontend server...
start "ToD Frontend" cmd /k "cd frontend && npm run dev"

:: Wait for frontend to start
timeout /t 5 /nobreak >nul

echo.
echo ============================================
echo   Game is starting!
echo ============================================
echo.
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo.
echo   Two terminal windows have opened.
echo   Close them (or run STOP_GAME.bat) to stop the game.
echo.

:: Open browser
start http://localhost:5173

echo Press any key to close this window...
pause >nul
