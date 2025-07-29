#!/bin/bash

# Shut down containers if running
docker-compose down
sleep 2
# Start containers in detached mode
docker-compose up -d

# Wait for Chroma or DBs to initialize
sleep 10

# Navigate to backend and start the API
cd backend
uvicorn app.main:app --port 8080 &
BACKEND_PID=$!

# Wait a moment and start frontend
cd ../frontend
pnpm dev &

# Optional: wait for background processes (or just let user ctrl+c)
wait $BACKEND_PID


