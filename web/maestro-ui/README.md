# Maestro Node UI

A React/TypeScript frontend for the Maestro workflow system.

## Prerequisites

- Python 3.8+
- Node.js and npm
- Git (to clone the repository)

## Installation

1. **Install Maestro:**
   ```bash
   pip install -e .
   ```

2. **Install UI dependencies:**
   ```bash
   cd web/maestro-ui
   npm install
   ```

3. **Configure environment** (for full functionality):
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```

## Quick Start

1. **Deploy with sample files:**
   ```bash
   maestro deploy tests/yamls/agents/openai_agent.yaml tests/yamls/workflows/openai_mcp_workflow.yaml --node-ui
   ```

2. **Open in browser:**
   ```
   http://localhost:5173
   ```

3. **Stop servers:**
   ```bash
   maestro clean
   ```

## Development

For custom agent and workflow files:

```bash
maestro deploy your-agents.yaml your-workflow.yaml --node-ui
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