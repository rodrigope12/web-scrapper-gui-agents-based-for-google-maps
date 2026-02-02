#!/bin/bash

# Start Backend
echo "Starting Backend..."
python -m uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!

# Start Worker
echo "Starting Worker..."
python -m backend.worker &
WORKER_PID=$!

# Start Frontend (Electron)
echo "Starting Frontend..."
cd frontend
npm run dev:electron &
FRONTEND_PID=$!

# Handle Exit
trap "kill $BACKEND_PID $FRONTEND_PID $WORKER_PID" EXIT

wait
