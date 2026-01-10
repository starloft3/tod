@echo off
echo ============================================
echo   Tides of Darkness - Installing Dependencies
echo ============================================
echo.

:: Get the directory where this script is located
cd /d "%~dp0"

:: Check for Python
echo Checking for Python...
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Python not found!
    echo.
    echo Please install Python 3.9 or higher:
    echo   1. Go to https://python.org/downloads
    echo   2. Download Python 3.11 (or latest 3.x)
    echo   3. Run the installer
    echo   4. IMPORTANT: Check "Add Python to PATH" at the bottom!
    echo   5. Click "Install Now"
    echo   6. Run this script again
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo   Found Python %PYVER%

:: Check for Node
echo Checking for Node.js...
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Node.js not found!
    echo.
    echo Please install Node.js:
    echo   1. Go to https://nodejs.org
    echo   2. Download the LTS version
    echo   3. Run the installer with default options
    echo   4. Run this script again
    echo.
    pause
    exit /b 1
)

for /f "tokens=1" %%i in ('node --version 2^>^&1') do set NODEVER=%%i
echo   Found Node.js %NODEVER%

echo.
echo ============================================
echo   Installing Python packages...
echo ============================================
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to install Python packages
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Installing Frontend packages...
echo ============================================
cd frontend
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to install frontend packages
    cd ..
    pause
    exit /b 1
)
cd ..

echo.
echo ============================================
echo   Installation Complete!
echo ============================================
echo.
echo You can now run START_GAME.bat to play.
echo.
pause
