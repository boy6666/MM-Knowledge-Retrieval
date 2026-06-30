@echo off
chcp 65001 >nul
title Device Maintenance System
color 0B

echo ============================================
echo   Device Maintenance Knowledge System
echo   Windows Startup Script
echo ============================================
echo.

:: ========== Step 1: Start backend ==========
echo [1/3] Starting backend...
echo.

cd /d "%~dp0backend"

if not exist "pyenv\Scripts\python.exe" (
    echo [INFO] Creating Python virtual environment...
    python -m venv pyenv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        echo        Make sure Python is installed and added to PATH.
        echo        Run: python --version
        pause
        exit /b 1
    )
)

echo [INFO] Installing Python packages...
call pyenv\Scripts\python.exe -m pip install -r requirements.txt -q

if not exist "data\uploads" mkdir data\uploads
if not exist "data\images" mkdir data\images

echo [INFO] Backend starting on http://localhost:8000
start "Backend" cmd /k "cd /d %~dp0backend && call pyenv\Scripts\activate && python main.py"
ping -n 5 127.0.0.1 >nul

:: ========== Step 2: Start frontend ==========
echo.
echo [2/3] Starting frontend...
echo.

cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo [INFO] Installing frontend packages...
    call npm install --no-audit --no-fund
)

echo [INFO] Frontend starting on http://localhost:3000
start "Frontend" cmd /k "cd /d %~dp0frontend && npx vite"

:: ========== Done ==========
echo.
echo [3/3] All services started!
echo.
echo ============================================
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo.
echo   First time? Create admin account:
echo     cd backend ^&^& pyenv\Scripts\activate ^&^& python create_admin.py
echo ============================================
echo.
pause
