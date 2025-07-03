# Maestro Builder

A modern web-based interface for building Maestro agents and workflows using AI assistance.

## Features

- **AI-Powered Chat Interface**: Chat with an AI assistant to help you create Maestro configurations
- **Real-time YAML Generation**: Automatically generates and updates `agents.yaml` and `workflow.yaml` files
- **Live Preview**: See your YAML configurations update in real-time as you chat
- **Persistent Chat Sessions**: Your conversations and YAML files are saved and can be resumed later
- **Diff Highlighting**: Visual diff view showing additions (green) and deletions (red) in YAML changes
- **Multiple View Modes**: Toggle between diff view, line numbers, and full YAML display
- **Save & Download**: Save your configurations locally or download YAML files
- **Modern UI**: Clean, responsive interface built with React and Tailwind CSS
- **API Integration**: Connects to the Maestro Builder API for intelligent responses

## Quick Start

### Option 1: Start Both API and Frontend (Recommended)

```bash
# From the builder directory
./start-dev.sh
```

This will start both the API server and the frontend development server automatically.

### Option 2: Start Components Separately

#### Start the API Server

```bash
# From the api directory
cd ../api
./run.sh
```

The API will be available at `http://localhost:8000`

#### Start the Frontend

```bash
# From the builder directory
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Usage

1. **Open the Builder**: Navigate to `http://localhost:5173` in your browser
2. **Start Chatting**: Type your requirements in the chat input at the bottom
3. **Watch YAML Generation**: See your `agents.yaml` and `workflow.yaml` files update in real-time
4. **View Changes**: Use the diff toggle to see highlighted changes (green for additions, red for deletions)
5. **Switch Views**: Toggle between diff view, line numbers, and full YAML display
6. **Save Your Work**: Use the save button to persist your configurations
7. **Download Files**: Use the download buttons in the YAML panel to save your configurations locally
8. **Manage Sessions**: Use the sidebar to switch between different chat sessions
9. **Create New Chats**: Click "New Chat" to start fresh with clean initial YAML files

## YAML Panel Features

### View Modes
- **Diff View** (Default): Shows changes with color-coded highlighting
  - 🟢 Green background/text for additions
  - 🔴 Red background/text for deletions
  - ⚪ Normal text for unchanged lines
- **Line Numbers**: Displays YAML with line numbers for easy reference
- **Full View**: Clean YAML display without diff or line numbers

### File Management
- **Always Shows Both Files**: `agents.yaml` and `workflow.yaml` are always visible
- **Initial Content**: New chats start with helpful comments explaining what each file is for
- **Save Button**: Persist your current YAML configurations
- **Download Button**: Download individual YAML files
- **Copy to Clipboard**: Quick copy functionality for each file

### Session Management
- **New Chat Creation**: Creates fresh sessions with clean initial YAML content
- **Chat History**: All conversations and generated files are automatically saved
- **Session Switching**: Seamlessly switch between different chat sessions
- **Session Deletion**: Remove old sessions while maintaining current work

## Example Conversations

### Creating an OpenAI Agent
```
User: "Create an OpenAI agent for text summarization"
AI: "I'll help you create an OpenAI agent for text summarization. Here's the configuration..."
```

### Building a Workflow
```
User: "Build a workflow that processes data and generates reports"
AI: "I'll create a workflow with multiple steps for data processing and report generation..."
```

### Complex Requirements
```
User: "Create a multi-agent system with a data processor, analyzer, and reporter"
AI: "I'll design a comprehensive multi-agent system with specialized roles..."
```

## API Integration

The builder connects to the Maestro Builder API which provides:

- **Intelligent Responses**: AI-powered chat responses using OpenAI (when API key is configured)
- **Fallback Mode**: Works without OpenAI API key using keyword-based responses
- **Session Management**: Maintains conversation context across messages with SQLite persistence
- **YAML Validation**: Ensures generated configurations follow Maestro schemas
- **Chat History**: Persistent storage of all conversations and generated YAML files

### API Endpoints

- `POST /api/chat_builder_agent` - Send chat messages and get responses
- `GET /api/get_yamls/{chat_id}` - Retrieve YAML files for a session
- `GET /api/chat_history` - Get chat history
- `POST /api/chat_continuation` - Continue an existing chat session

## Configuration

### Environment Variables

Set these in the API directory:

```bash
export OPENAI_API_KEY="your-openai-api-key"
```

### API Configuration

The API runs on `http://localhost:8000` by default. You can modify the URL in `src/services/api.ts` if needed.

### Database

The API uses SQLite for persistent storage of:
- Chat sessions
- Message history
- Generated YAML files

The database file is automatically created in the API directory.

## Development

### Project Structure

```
builder/
├── src/
│   ├── components/
│   │   ├── ChatCanvas.tsx      # Chat message display
│   │   ├── ChatInput.tsx       # Message input component
│   │   ├── Sidebar.tsx         # Chat history sidebar
│   │   └── YamlPanel.tsx       # YAML file display with diff
│   ├── services/
│   │   └── api.ts             # API integration service
│   └── App.tsx                # Main application
├── start-dev.sh               # Development startup script
└── package.json
```

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `./start-dev.sh` - Start both API and frontend

## Troubleshooting

### API Connection Issues

1. Ensure the API server is running on `http://localhost:8000`
2. Check that CORS is properly configured in the API
3. Verify the API endpoint in `src/services/api.ts`

### YAML Not Updating

1. Check the browser console for errors
2. Verify the API response format
3. Ensure the YAML panel is properly connected

### Diff Not Showing Colors

1. Check that you're in diff mode (toggle button in YAML panel)
2. Ensure there are actual changes to display
3. Check browser console for any JavaScript errors

### OpenAI Integration

1. Set your `OPENAI_API_KEY` environment variable
2. Restart the API server after setting the key
3. Check API logs for authentication errors

### Database Issues

1. Check that the API has write permissions in its directory
2. Verify SQLite is properly installed
3. Check API logs for database connection errors

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test the integration
5. Submit a pull request

## License

This project is part of the Maestro framework and follows the same license terms.
