@echo off
echo ========================================================
echo Starting Fragrance Finder
echo ========================================================

echo Starting Database and Services (Docker)...
docker compose up -d
timeout /t 5 /nobreak > nul

echo Starting Backend API...
start cmd /k "title Fragrance Finder Backend && cd backend && .venv\Scripts\python.exe -m uvicorn main:app --reload"

echo Starting Frontend Next.js Server...
start cmd /k "title Fragrance Finder Frontend && cd frontend && set PORT=3001 && npm run dev"

echo Starting Scraper Daemon...
start cmd /k "title Fragrance Finder Scraper && cd backend && set PYTHONIOENCODING=utf-8 && .venv\Scripts\python.exe scraper.py"

echo.
echo All services have been launched in new windows!
echo You can now access the app at: http://localhost:3001
echo ========================================================
