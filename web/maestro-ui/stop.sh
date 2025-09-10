#!/bin/sh

kill_port() {
  port=$1
  pids=$(lsof -t -i :$port 2>/dev/null)
  if [ -n "$pids" ]; then
    echo "Killing processes on port $port: $pids"
    kill -9 $pids 2>/dev/null || true
  else
    echo "No process on port $port"
  fi
}

# Kill maestro processes using environment variables or defaults
kill_port ${MAESTRO_PORT:-8000}
kill_port ${MAESTRO_UI_PORT:-5173}

# Kill any remaining Vite/npm dev processes
vite_pids=$(ps aux | grep -E "(vite|npm.*dev)" | grep -v grep | awk '{print $2}')
if [ -n "$vite_pids" ]; then
  echo "Killing Vite dev processes: $vite_pids"
  kill -9 $vite_pids 2>/dev/null || true
fi

docker_pids=$(docker ps -q --filter ancestor=maestro-ui 2>/dev/null)
if [ -n "$docker_pids" ]; then
  echo "Stopping Docker UI containers: $docker_pids"
  docker stop $docker_pids >/dev/null 2>&1 || true
fi

for port in 3000 4000 5173 8080 9000; do
  pids=$(lsof -t -i :$port 2>/dev/null)
  if [ -n "$pids" ]; then
    for pid in $pids; do
      cmd=$(ps -p $pid -o comm= 2>/dev/null)
      if echo "$cmd" | grep -qE "(node|vite|nginx)"; then
        echo "Killing UI process on port $port (PID $pid): $cmd"
        kill -9 $pid 2>/dev/null || true
      fi
    done
  fi
done


echo "Cleanup complete."


