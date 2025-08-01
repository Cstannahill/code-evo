#!/bin/bash

# Shut down containers if running
docker-compose down
sleep 2
# Start containers in detached mode
docker-compose up -d

# Wait for Chroma or DBs to initialize
sleep 10

# Start frontend first
cd frontend
pnpm dev &
FRONTEND_PID=$!
cd ..

# Start backend
cd backend
uvicorn app.main:app --port 8080 --reload &
BACKEND_PID=$!
cd ..

# Optional: wait for backend process (or both)
wait $BACKEND_PID