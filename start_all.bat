@echo off
chcp 65001 >nul
title Device Maintenance System
color 0B

echo ============================================
echo   Device Maintenance Knowledge System
echo   Full Stack Startup Script
echo ============================================
echo.

:: ========== 1. Check PostgreSQL ==========
echo [1/4] Checking PostgreSQL...
D:\software\PostgreSQL\bin\pg_isready -h 127.0.0.1 >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] PostgreSQL is running
) else (
    echo [WARN] PostgreSQL not responding. Try: net start postgresql-x64-18
    echo        (Run PowerShell as Administrator)
)

:: ========== 2. Start AI Core (:8001) ==========
echo.
echo [2/4] Starting AI Core on :8001...
start "AI-Core" cmd /k "D:\Anaconda2025.06\envs\mm-ai\python.exe ai-core\main.py"
ping -n 4 127.0.0.1 >nul

:: Check if AI Core is up
curl -s http://localhost:8001/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] AI Core is running
) else (
    echo [WARN] AI Core may not be ready yet
)

:: ========== 3. Start Java Backend (:8080) ==========
echo.
echo [3/4] Starting Java Backend on :8080...
cd /d "%~dp0backend-java"
start "Java-Backend" cmd /k "mvnw spring-boot:run -q"
ping -n 8 127.0.0.1 >nul

:: Check if Java Backend is up
curl -s http://localhost:8080/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Java Backend is running
) else (
    echo [WARN] Java Backend may not be ready yet (takes 10-20s)
)

:: ========== 4. Start Frontend (:3000) ==========
echo.
echo [4/4] Starting Frontend on :3000...
cd /d "%~dp0frontend"
if not exist "node_modules" (
    echo [INFO] Installing frontend packages...
    call npm install --no-audit --no-fund
)
start "Frontend" cmd /k "npx vite --host"

:: ========== Done ==========
echo.
echo ============================================
echo   All services started!
echo.
echo   Backend:  http://localhost:8080
echo   AI Core:  http://localhost:8001
echo   Frontend: http://localhost:3000
echo.
echo   Health check:
echo     curl http://localhost:8080/health
echo     curl http://localhost:8001/health
echo.
echo   Stop: close each window or use taskkill
echo ============================================
echo.
pause
