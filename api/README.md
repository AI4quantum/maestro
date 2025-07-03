# Maestro Builder API

A FastAPI application that provides backend services for the Maestro Builder frontend application. This API enables intelligent YAML generation for Maestro agents and workflows through conversational AI.

## Features

- **Chat Builder Agent**: Conversational AI interface for creating Maestro YAML configurations
- **YAML Management**: Generate and manage `agents.yaml` and `workflow.yaml` files
- **Chat History**: Persistent storage of chat conversations
- **Session Management**: Support for multiple chat sessions
- **Maestro Integration**: Leverages existing Maestro agent framework

## API Endpoints

### 1. Chat Builder Agent
- **POST** `/api/chat_builder_agent`
- **Description**: Chat with the AI agent to generate YAML configurations
- **Parameters**:
  - `message`: Chat message from the user
  - `chat_id` (optional): Continue existing conversation
- **Returns**: AI response and updated YAML files

### 2. Get YAML Files
- **GET** `/api/get_yamls/{chat_id}`
- **Description**: Retrieve YAML files for a specific chat session
- **Parameters**:
  - `chat_id`: The chat session ID
- **Returns**: List of YAML files with their content

### 3. Chat History
- **GET** `/api/chat_history`
- **Description**: Get history of all chat conversations
- **Returns**: List of chat history entries

## Installation

1. **Install Dependencies**:
   ```bash
   cd api
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

3. **Run the API**:
   ```bash
   python main.py
   ```

   Or using uvicorn directly:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Usage

### Starting the API Server

The API will be available at `http://localhost:8000`

### API Documentation

Once running, you can access:
- **Interactive API docs**: `http://localhost:8000/docs`
- **ReDoc documentation**: `http://localhost:8000/redoc`

### Example API Calls

#### Start a new chat:
```bash
curl -X POST "http://localhost:8000/api/chat_builder_agent" \
     -H "Content-Type: application/json" \
     -d '{"content": "Create an OpenAI agent for text summarization"}'
```

#### Continue an existing chat:
```bash
curl -X POST "http://localhost:8000/api/chat_builder_agent" \
     -H "Content-Type: application/json" \
     -d '{"content": "Add a workflow step", "chat_id": "existing-chat-id"}'
```

#### Get YAML files:
```bash
curl "http://localhost:8000/api/get_yamls/your-chat-id"
```

#### Get chat history:
```bash
curl "http://localhost:8000/api/chat_history"
```

## Architecture

### Components

1. **FastAPI Application** (`main.py`): Main API server with endpoints
2. **AI Agent** (`ai_agent.py`): Intelligent YAML generation using Maestro's agent framework
3. **Storage System**: File-based storage for chat sessions and history
4. **CORS Middleware**: Enables frontend communication

### Data Flow

1. User sends message to `/api/chat_builder_agent`
2. API loads or creates chat session
3. AI agent processes message and generates YAML updates
4. Session is saved with updated YAML files
5. Response includes AI message and updated YAML content

### Storage

- **Chat Sessions**: Stored as JSON files in `api/storage/`
- **Chat History**: Centralized history file `api/storage/chat_history.json`
- **File Format**: JSON with timestamps and structured data

## Integration with Maestro

The API integrates with the existing Maestro framework:

- **Agent Framework**: Uses Maestro's `OpenAIAgent` for intelligent responses
- **YAML Schemas**: Follows Maestro's agent and workflow schemas
- **Validation**: Validates generated YAML against expected structures
- **Environment Variables**: Uses Maestro's environment variable patterns

## Development

### Project Structure
```
api/
├── main.py              # FastAPI application
├── ai_agent.py          # AI agent for YAML generation
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── storage/            # Chat session storage (created at runtime)
    ├── chat_*.json     # Individual chat sessions
    └── chat_history.json # Chat history
```

### Adding New Features

1. **New Endpoints**: Add to `main.py`
2. **AI Logic**: Extend `ai_agent.py`
3. **Data Models**: Update Pydantic models in `main.py`
4. **Storage**: Extend storage functions as needed

### Testing

```bash
# Test the API endpoints
curl http://localhost:8000/

# Test chat functionality
curl -X POST "http://localhost:8000/api/chat_builder_agent" \
     -H "Content-Type: application/json" \
     -d '{"content": "test message"}'
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: OpenAI API key for AI agent functionality
- `PORT`: API server port (default: 8000)
- `HOST`: API server host (default: 0.0.0.0)

### CORS Configuration

The API is configured to allow requests from:
- `http://localhost:5173` (Vite default)
- `http://localhost:3000` (Alternative dev server)

## Production Deployment

For production deployment:

1. **Use a production ASGI server** (e.g., Gunicorn with Uvicorn workers)
2. **Implement proper database storage** instead of file-based storage
3. **Add authentication and authorization**
4. **Configure proper CORS origins**
5. **Add rate limiting and monitoring**
6. **Use environment-specific configuration**

Example production command:
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure Maestro source is in Python path
2. **API Key Issues**: Verify `OPENAI_API_KEY` is set correctly
3. **CORS Errors**: Check frontend origin matches CORS configuration
4. **Storage Errors**: Ensure `api/storage/` directory is writable

### Logs

The API provides detailed error messages and warnings:
- AI agent initialization status
- Session loading/saving operations
- YAML validation results

## Contributing

1. Follow the existing code structure
2. Add proper error handling
3. Update documentation for new features
4. Test with the frontend application
5. Validate YAML generation against Maestro schemas 