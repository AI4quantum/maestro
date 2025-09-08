#!/bin/sh

# Stop FastAPI (8000), Vite dev (5173), and NGINX UI (8080) if running
# Also stop optional Docker UI container if MAESTRO_UI_IMAGE is provided

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

kill_port 8000   # FastAPI (backend)
kill_port 5173   # Vite dev UI

# Kill prod UI port only when using Dockerized UI
if [ "${MAESTRO_UI_MODE}" = "prod" ] || [ -n "${MAESTRO_UI_PORT}" ]; then
  kill_port ${MAESTRO_UI_PORT:-8080}
fi

# Stop Dockerized UI container by image name (best-effort)
if [ -n "$MAESTRO_UI_IMAGE" ]; then
  cid=$(docker ps -q --filter ancestor=$MAESTRO_UI_IMAGE)
  if [ -n "$cid" ]; then
    echo "Stopping container $cid for image $MAESTRO_UI_IMAGE"
    docker stop $cid >/dev/null 2>&1 || true
  fi
fi

echo "Cleanup complete."


