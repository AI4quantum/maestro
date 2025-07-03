#!/bin/bash

# Maestro Start Script
# Starts both the API and Builder frontend services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for a service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            print_success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within $((max_attempts * 2)) seconds"
    return 1
}

# Check if services are already running
if check_port 8000; then
    print_warning "API service is already running on port 8000"
fi

if check_port 5173; then
    print_warning "Builder frontend is already running on port 5173"
fi

# Start API service
print_status "Starting Maestro API service..."

# Check if we're in the right directory structure
if [ ! -d "api" ]; then
    print_error "API directory not found. Please run this script from the Maestro root directory."
    exit 1
fi

cd api

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed."
    exit 1
fi

# Check if requirements are installed
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    print_status "Setting up virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    # Activate existing virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
fi

# Create storage directory if it doesn't exist
mkdir -p storage

# Start API server in background
print_status "Starting API server on http://localhost:8000"
nohup python main.py > ../logs/api.log 2>&1 &
API_PID=$!
echo $API_PID > ../logs/api.pid

print_success "API service started with PID: $API_PID"

# Go back to root directory
cd ..

# Start Builder frontend
print_status "Starting Maestro Builder frontend..."

# Check if we're in the right directory structure
if [ ! -d "builder" ]; then
    print_error "Builder directory not found. Please run this script from the Maestro root directory."
    exit 1
fi

cd builder

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    print_error "Node.js is required but not installed."
    exit 1
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    print_error "npm is required but not installed."
    exit 1
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    print_status "Installing npm dependencies..."
    npm install
fi

# Start the development server in background
print_status "Starting Builder frontend on http://localhost:5173"
nohup npm run dev > ../logs/builder.log 2>&1 &
BUILDER_PID=$!
echo $BUILDER_PID > ../logs/builder.pid

print_success "Builder frontend started with PID: $BUILDER_PID"

# Go back to root directory
cd ..

# Wait for services to be ready
print_status "Waiting for services to be ready..."

if wait_for_service "http://localhost:8000" "API service"; then
    print_success "API service is ready at http://localhost:8000"
    print_status "API documentation available at http://localhost:8000/docs"
else
    print_error "API service failed to start properly"
    exit 1
fi

if wait_for_service "http://localhost:5173" "Builder frontend"; then
    print_success "Builder frontend is ready at http://localhost:5173"
else
    print_error "Builder frontend failed to start properly"
    exit 1
fi

print_success "All Maestro services are now running!"
echo ""
echo "Services:"
echo "  - API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Builder Frontend: http://localhost:5173"
echo ""
echo "Logs:"
echo "  - API logs: logs/api.log"
echo "  - Builder logs: logs/builder.log"
echo ""
echo "To stop all services, run: ./stop.sh"
echo "To view logs, run: tail -f logs/api.log or tail -f logs/builder.log" 