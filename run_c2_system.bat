@echo off
setlocal
cd /d "%~dp0"
title Sentinel Vision AI - C2 Launcher
cls

echo ===============================================================================
echo            SHREE GUJARAT HACKATHON 2026 // SENTINEL VISION AI
echo         Unified C2 Surveillance System (Model 2 AI + Model 3 VMS)
echo ===============================================================================
echo.
echo Select execution mode:
echo.
echo [1] LAUNCH EVERYTHING IN 1-CLICK (FastAPI + React GUI + AI Engine + Browser)
echo.
echo [2] Start React GUI + FastAPI Backend Only (Without Camera RTSP Pipeline)
echo [3] Start Master AI Vision Pipeline Only (main.py)
echo [4] Start FastAPI C2 Gateway Only (server.py)
echo [5] Start React Tactical Frontend Only (npm run dev)
echo [6] Docker Compose Deploy (Full Containerized Stack)
echo [7] Exit
echo.
echo ===============================================================================

set "choice=1"
set /p "choice=Enter choice [Default: 1]: "

if "%choice%"=="1" goto opt1
if "%choice%"=="2" goto opt2
if "%choice%"=="3" goto opt3
if "%choice%"=="4" goto opt4
if "%choice%"=="5" goto opt5
if "%choice%"=="6" goto opt6
if "%choice%"=="7" goto end
goto opt1

:opt1
echo.
echo [*] Launching Full Sentinel Vision AI Stack...
echo [*] 1/3 Starting FastAPI C2 Gateway on port 8000...
start "Sentinel C2 Backend Gateway" cmd /k ".\.venv\Scripts\python.exe -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload"

echo [*] 2/3 Starting React Tactical GUI on port 5173...
start "Sentinel C2 Frontend" cmd /k "cd frontend && npm run dev"

echo [*] 3/3 Starting Master AI Vision Pipeline (Headless Web Relay Mode)...
start "Sentinel Vision AI Engine" cmd /k ".\.venv\Scripts\python.exe main.py --headless"

echo [*] Waiting for services to initialize...
ping 127.0.0.1 -n 5 >nul

echo [*] Opening Command and Control GUI in your browser...
start http://localhost:5173

echo.
echo ===============================================================================
echo [SUCCESS] All systems active!
echo   - GUI:              http://localhost:5173
echo   - API Gateway Docs: http://localhost:8000/docs
echo   - Telemetry Stream: ws://localhost:8000/ws/telemetry
echo ===============================================================================
pause
goto end

:opt2
echo.
echo [*] Starting FastAPI Backend + React GUI...
start "Sentinel C2 Backend Gateway" cmd /k ".\.venv\Scripts\python.exe -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload"
start "Sentinel C2 Frontend" cmd /k "cd frontend && npm run dev"

ping 127.0.0.1 -n 3 >nul
start http://localhost:5173
pause
goto end

:opt3
echo.
echo [*] Starting Master AI Vision Pipeline...
call .\.venv\Scripts\python.exe main.py
pause
goto end

:opt4
echo.
echo [*] Starting FastAPI C2 Gateway on http://localhost:8000...
call .\.venv\Scripts\python.exe -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
pause
goto end

:opt5
echo.
echo [*] Starting React Tactical GUI on http://localhost:5173...
cd frontend
npm run dev
pause
goto end

:opt6
echo.
echo [*] Building and deploying Docker containers...
docker compose up --build
pause
goto end

:end
exit /b 0
