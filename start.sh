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
        echo -n "[INFO] $name: attempt $attempt..."
        if curl -s "$url" >/dev/null 2>&1; then
            echo ""
            print_success "$name is ready!"
            return 0
        fi
        sleep 2
        attempt=$((attempt + 1))
    done

    echo ""
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

VENV_PYTHON="/Users/gliu/Desktop/work/maestro/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
    print_error "Expected Python binary not found at $VENV_PYTHON"
    exit 1
fi

mkdir -p storage

print_status "Starting API server on http://localhost:8001"
nohup "$VENV_PYTHON" main.py > ../logs/api.log 2>&1 &
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

NODE_VERSION=$(node -v | cut -d 'v' -f2 | cut -d '.' -f1)
if [ "$NODE_VERSION" -lt 20 ]; then
    print_error "Node.js v20+ is required. Current version: $(node -v)"
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
