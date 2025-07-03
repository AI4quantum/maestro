#!/bin/bash

# Maestro Builder Development Startup Script
# This script starts both the API server and the frontend development server

echo "Starting Maestro Builder Development Environment..."

# Function to cleanup background processes on exit
cleanup() {
    echo "Shutting down development servers..."
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check if we're in the builder directory
if [ ! -f "package.json" ]; then
    echo "Error: package.json not found. Please run this script from the builder directory."
    exit 1
fi

# Check if API directory exists
if [ ! -d "../api" ]; then
    echo "Error: API directory not found. Please ensure the api directory exists."
    exit 1
fi

echo "Starting API server..."

# Start API server in background
cd ../api
if [ -f "run.sh" ]; then
    chmod +x run.sh
    ./run.sh &
else
    echo "Error: run.sh not found in api directory"
    exit 1
fi

API_PID=$!
cd ../builder

echo "API server started with PID: $API_PID"
echo "Waiting for API to be ready..."

# Wait for API to be ready
sleep 5

echo "Starting frontend development server..."

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start frontend development server
npm run dev &
FRONTEND_PID=$!

echo "Frontend server started with PID: $FRONTEND_PID"
echo ""
echo "Development environment is ready!"
echo "API server: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for both processes
wait 