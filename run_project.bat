@echo off
TITLE Hikvision Smart Vision - Startup Script
COLOR 0C

echo ===================================================
echo   HIKVISION SMART VISION SYSTEM - DEV STARTUP
echo ===================================================
echo.

:: 1. Start Backend Server
echo [1/3] Launching Python Backend (FastAPI)...
start cmd /k "cd /d "%~dp0backend" && python main.py"

:: 2. Start Frontend Server
echo [2/3] Launching React Frontend (Vite)...
start cmd /k "cd /d "%~dp0frontend" && npm run dev"

:: 3. Give servers a moment to initialize
echo [3/3] Waiting for servers to initialize...
timeout /t 5 /nobreak > nul

:: 4. Open Browser
echo Opening Industrial Dashboard at http://localhost:5173/
start http://localhost:5173/

echo.
echo ===================================================
echo   SYSTEM ENGAGED. DO NOT CLOSE THE BACKGROUND WINDOWS.
echo.
echo   [NOTE: If you want to run the application hosted
echo   statically, simply run 'python main.py' alone and
echo   navigate to http://localhost:8000]
echo ===================================================
pause
