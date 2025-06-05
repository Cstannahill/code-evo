<<<<<<< HEAD
docker-compose down
=======
>>>>>>> a1d19c7f56b54abd7bf7560156fcb17ab40fd16c
docker-compose up -d
@echo off
REM Navigate to the backend directory and start the backend server
cd backend
python -m uvicorn app.main:app --port 8080
<<<<<<< HEAD
=======
cd ../frontend
pnpm dev
>>>>>>> a1d19c7f56b54abd7bf7560156fcb17ab40fd16c
