docker-compose up -d
@echo off
REM Navigate to the backend directory and start the backend server
cd backend
python -m uvicorn app.main:app --port 8080
cd ../frontend
pnpm dev