# Maestro Node UI (Dev/Prod)

## Dev (Vite)

- Prereqs: Python venv active, backend config (e.g., OPENAI_API_KEY)
- Start: `maestro deploy agents.yaml workflow.yaml --node-ui --ui-mode dev`
- Open: `http://localhost:5173`
- Stop: `bash web/maestro-ui/stop.sh`

## Prod (Dockerized)

- Start: `MAESTRO_UI_IMAGE=maestro-ui:dev MAESTRO_UI_PORT=8080 maestro deploy agents.yaml workflow.yaml --node-ui --ui-mode prod`
- Open: `http://localhost:8080`
- Stop: `bash web/maestro-ui/stop.sh` (kills 8000 and 8080 when prod)

## Endpoints

- `POST /chat`, `POST /chat/stream`, `GET /health`, `GET /diagram` (FastAPI workflow server)

## Notes

- `stop.sh` cleans up FastAPI (8000), Vite (5173), and Docker UI (8080 in prod).
- For CORS in backend: `export CORS_ALLOW_ORIGINS=http://localhost:5173`.
