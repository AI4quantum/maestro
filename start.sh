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

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

mkdir -p logs

check_port() {
    local port=$1
    lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1
}

wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1

    print_status "Waiting for $name to be ready..."

    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            print_success "$name is ready!"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    print_error "$name failed to start within $((max_attempts * 2)) seconds"
    return 1
}

# Warn if services are already running
check_port 8000 && print_warning "API already running on port 8000"
(check_port 5174 || check_port 5173) && print_warning "Builder frontend already running on port 5174 or 5173"

### ───────────── Start API ─────────────

print_status "Starting Maestro API service..."

if [ ! -d "api" ]; then
    print_error "API directory not found. Run this script from the Maestro root directory."
    exit 1
fi

cd api

if ! command -v python3 &>/dev/null; then
    print_error "Python 3 is required but not installed."
    exit 1
fi

if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate 2>/dev/null || source .venv/bin/activate
fi



mkdir -p storage

print_status "Starting API server on http://localhost:8001"
# nohup python main.py > ../logs/api.log 2>&1 &

# TODO: FIX THIS
nohup /Users/gliu/Desktop/work/maestro/.venv/bin/python main.py > ../logs/api.log 2>&1 &
API_PID=$!
echo $API_PID > ../logs/api.pid

print_success "API service started with PID: $API_PID"

cd ..

### ───────────── Start Builder ─────────────

print_status "Starting Maestro Builder frontend..."

if [ ! -d "builder" ]; then
    print_error "Builder directory not found. Run this script from the Maestro root directory."
    exit 1
fi

cd builder

if ! command -v node &>/dev/null; then
    print_error "Node.js is required but not installed."
    exit 1
fi

if ! command -v npm &>/dev/null; then
    print_error "npm is required but not installed."
    exit 1
fi

if [ ! -d "node_modules" ]; then
    print_status "Installing frontend dependencies..."
    npm install
fi

print_status "Starting Builder frontend on http://localhost:5174"
nohup npm run dev > ../logs/builder.log 2>&1 &
BUILDER_PID=$!
echo $BUILDER_PID > ../logs/builder.pid

print_success "Builder frontend started with PID: $BUILDER_PID"

cd ..

### ───────────── Wait for Services ─────────────

print_status "Waiting for services to be ready..."

if wait_for_service "http://localhost:8001/api/health" "API service"; then
    print_success "API is ready at http://localhost:8001"
    print_status "API docs: http://localhost:8001/docs"
else
    print_error "API service failed to start"
    exit 1
fi

if wait_for_service "http://localhost:5174" "Builder frontend"; then
    print_success "Builder frontend is ready at http://localhost:5174"
else
    print_error "Builder frontend failed to start"
    exit 1
fi

### ───────────── Summary ─────────────

print_success "All Maestro services are now running!"
echo ""
echo "Services:"
echo "  - API: http://localhost:8001"
echo "  - API Docs: http://localhost:8001/docs"
echo "  - Builder Frontend: http://localhost:5174"
echo ""
echo "Logs:"
echo "  - API: logs/api.log"
echo "  - Builder: logs/builder.log"
echo ""
echo "To stop all services, run: ./stop.sh"
echo "To view logs: tail -f logs/api.log | logs/builder.log"