@echo off
echo ============================================================
echo  CRUZR TWIN DNTU02 - AUTOMATIC SYSTEM STARTER
echo ============================================================
echo.

echo [1/2] Starting Flask Backend Server (Port 5000)...
start "Flask Backend Webhook" cmd /k "env\Scripts\python src\fiware\webhook_receiver.py"

echo [2/2] Starting React Frontend Dashboard (Port 5173)...
cd frontend
start "React Frontend" cmd /k "npm run dev"

echo.
echo ============================================================
echo  SYSTEM IS RUNNING!
echo  Dashboard URL: http://localhost:5173
echo ============================================================
start http://localhost:5173
