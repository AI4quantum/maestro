# Maestro Node UI

A React/TypeScript frontend for the Maestro workflow system.

## Setup

First, install the UI dependencies:

```bash
cd web/maestro-ui
npm install
```

## Development

### Prerequisites
- Python virtual environment activated
- Backend configuration (e.g., `OPENAI_API_KEY` environment variable)
- UI dependencies installed (see Setup above)

### Running the UI

1. **Start both API and UI servers:**
   ```bash
   maestro deploy agents.yaml workflow.yaml --node-ui
   ```

2. **Open in browser:**
   ```
   http://localhost:5173
   ```

3. **Stop servers:**
   ```bash
   maestro clean
   ```

## Production (Docker)

- **Start:** `MAESTRO_UI_IMAGE=maestro-ui:dev MAESTRO_UI_PORT=8080 maestro deploy agents.yaml workflow.yaml --node-ui`
- **Open:** `http://localhost:8080`
- **Stop:** `maestro clean`

## API Endpoints

The backend provides the following endpoints:

- `POST /chat` - Send chat messages
- `POST /chat/stream` - Stream chat responses  
- `GET /health` - Health check
- `GET /diagram` - Get workflow diagram

## Notes

- The `maestro clean` command dynamically cleans up all Maestro-related processes including FastAPI servers, Vite dev servers, and Docker containers
- For CORS configuration, the system automatically sets `CORS_ALLOW_ORIGINS=http://localhost:5173` when using `--node-ui`
- The `--node-ui` flag automatically starts both the FastAPI backend and the Vite frontend development server