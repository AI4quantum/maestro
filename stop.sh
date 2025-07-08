#!/bin/bash

# Maestro Stop Script
# Safely stops both the API and Builder frontend services

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

# Function to check if a process is running
is_process_running() {
    local pid=$1
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0  # Process is running
    else
        return 1  # Process is not running
    fi
}

# Function to safely stop a process
stop_process() {
    local pid_file=$1
    local service_name=$2
    local port=$3
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        
        if is_process_running "$pid"; then
            print_status "Stopping $service_name (PID: $pid)..."
            
            # Try graceful shutdown first
            kill "$pid" 2>/dev/null || true
            
            # Wait for graceful shutdown
            local wait_count=0
            while is_process_running "$pid" && [ $wait_count -lt 10 ]; do
                sleep 1
                wait_count=$((wait_count + 1))
            done
            
            # Force kill if still running
            if is_process_running "$pid"; then
                print_warning "$service_name didn't stop gracefully, forcing termination..."
                kill -9 "$pid" 2>/dev/null || true
                sleep 1
            fi
            
            if is_process_running "$pid"; then
                print_error "Failed to stop $service_name (PID: $pid)"
                return 1
            else
                print_success "$service_name stopped successfully"
                rm -f "$pid_file"
                return 0
            fi
        else
            print_warning "$service_name is not running (PID: $pid)"
            rm -f "$pid_file"
            return 0
        fi
    else
        print_warning "PID file for $service_name not found"
        return 0
    fi
}

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill processes by port
kill_process_by_port() {
    local port=$1
    local service_name=$2
    
    if check_port "$port"; then
        print_warning "$service_name is still running on port $port, attempting to kill by port..."
        local pids=$(lsof -ti :$port 2>/dev/null || true)
        
        if [ -n "$pids" ]; then
            for pid in $pids; do
                print_status "Killing process $pid on port $port..."
                kill -9 "$pid" 2>/dev/null || true
            done
            
            # Wait a moment and check again
            sleep 2
            if check_port "$port"; then
                print_error "Failed to stop $service_name on port $port"
                return 1
            else
                print_success "$service_name stopped on port $port"
                return 0
            fi
        else
            print_error "Could not find process using port $port"
            return 1
        fi
    else
        print_success "$service_name is not running on port $port"
        return 0
    fi
}

print_status "Stopping Maestro services..."

# Stop API service
if [ -f "logs/api.pid" ]; then
    stop_process "logs/api.pid" "API service" 8000
else
    print_warning "API PID file not found, checking port 8000..."
    kill_process_by_port 8000 "API service"
fi

# Stop Builder frontend
if [ -f "logs/builder.pid" ]; then
    stop_process "logs/builder.pid" "Builder frontend" 5174
    stop_process "logs/builder.pid" "Builder frontend" 5174
else
    print_warning "Builder PID file not found, checking port 5174..."
    kill_process_by_port 5174 "Builder frontend"
fi

# Final verification
echo ""
print_status "Verifying services are stopped..."

api_stopped=true
builder_stopped=true

if check_port 8000; then
    print_error "API service is still running on port 8000"
    api_stopped=false
fi

if check_port 5174 || check_port 5173; then
    print_error "Builder frontend is still running on port 5174 or 5173"
    builder_stopped=false
fi

if [ "$api_stopped" = true ] && [ "$builder_stopped" = true ]; then
    print_success "All Maestro services have been stopped successfully!"
else
    print_error "Some services may still be running. You may need to manually stop them."
    exit 1
fi

# Clean up log files if they exist
if [ -f "logs/api.log" ]; then
    print_status "API logs are available at: logs/api.log"
fi

if [ -f "logs/builder.log" ]; then
    print_status "Builder logs are available at: logs/builder.log"
fi

echo ""
echo "To start services again, run: ./start.sh" 