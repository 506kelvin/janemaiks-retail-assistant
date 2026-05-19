@echo off
echo.
echo  ========================================
echo     JaneMaiks Retail Assistant
echo     AI-Powered Retail Management System
echo  ========================================
echo.
echo [1/2] Starting Backend (FastAPI)...
start "JaneMaiks Backend" cmd /c "cd /d %~dp0backend && venv\Scripts\activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo [2/2] Starting Frontend (Vite)...
start "JaneMaiks Frontend" cmd /c "cd /d %~dp0frontend && npm run dev"

echo.
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:5173
echo  API Docs: http://localhost:8000/docs
echo.
echo  Welcome to JaneMaiks!
echo.
