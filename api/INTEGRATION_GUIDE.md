# Maestro Builder API Integration Guide

This guide explains how to integrate the Maestro Builder API with the existing frontend application.

## Quick Start

1. **Start the API server**:
   ```bash
   cd api
   python main.py
   ```

2. **Update the frontend** to use the API instead of the mock implementation.

## API Endpoints

### 1. Chat Builder Agent
- **URL**: `POST /api/chat_builder_agent`
- **Purpose**: Send messages to the AI agent and get YAML updates
- **Request Body**:
  ```json
  {
    "content": "Create an OpenAI agent for text summarization",
    "role": "user"
  }
  ```
- **Response**:
  ```json
  {
    "response": "I'll help you create an OpenAI agent for text summarization...",
    "yaml_files": [
      {
        "name": "agents.yaml",
        "content": "# Agents configuration..."
      },
      {
        "name": "workflow.yaml", 
        "content": "# Workflow configuration..."
      }
    ]
  }
  ```

### 2. Get YAML Files
- **URL**: `GET /api/get_yamls/{chat_id}`
- **Purpose**: Retrieve YAML files for a specific chat session
- **Response**: Array of YAML files with name and content

### 3. Chat History
- **URL**: `GET /api/chat_history`
- **Purpose**: Get list of all chat conversations
- **Response**: Array of chat history entries

## Frontend Integration

### Step 1: Install the API Client

Copy the `frontend_integration_example.ts` file to your frontend project and import it:

```typescript
import MaestroBuilderAPI from './api/MaestroBuilderAPI';
```

### Step 2: Update App.tsx

Replace the mock `handleSendMessage` function in `builder/src/App.tsx`:

```typescript
import MaestroBuilderAPI from '../api/frontend_integration_example';

// Initialize the API client
const api = new MaestroBuilderAPI();

const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content,
        timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    
    try {
        const result = await api.sendMessage(content);
        
        const assistantMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: result.response,
            timestamp: new Date()
        };
        
        setMessages(prev => [...prev, assistantMessage]);
        
        // Update YAML files
        setYamlFiles(result.yaml_files.map(file => ({
            name: file.name,
            content: file.content,
            language: 'yaml' as const
        })));
        
    } catch (error) {
        console.error('Error sending message:', error);
        // Handle error appropriately (show notification, etc.)
    }
};
```

### Step 3: Add Chat History Support

Add a function to load chat history:

```typescript
const loadChatHistory = async () => {
    try {
        const history = await api.getChatHistory();
        // Update your UI to show chat history
        console.log('Chat history:', history);
    } catch (error) {
        console.error('Error loading chat history:', error);
    }
};

// Call this in useEffect or when component mounts
useEffect(() => {
    loadChatHistory();
}, []);
```

### Step 4: Add YAML File Loading

Add a function to load YAML files for a specific chat:

```typescript
const loadYamlFiles = async (chatId: string) => {
    try {
        const yamlFiles = await api.getYamlFiles(chatId);
        setYamlFiles(yamlFiles.map(file => ({
            name: file.name,
            content: file.content,
            language: 'yaml' as const
        })));
    } catch (error) {
        console.error('Error loading YAML files:', error);
    }
};
```

## Error Handling

The API client includes error handling, but you should add user-friendly error messages:

```typescript
const handleSendMessage = async (content: string) => {
    // ... existing code ...
    
    try {
        const result = await api.sendMessage(content);
        // ... handle success ...
    } catch (error) {
        console.error('Error sending message:', error);
        
        // Show user-friendly error message
        const errorMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: 'Sorry, I encountered an error. Please try again.',
            timestamp: new Date()
        };
        
        setMessages(prev => [...prev, errorMessage]);
    }
};
```

## Environment Configuration

### Development

For development, the API runs on `http://localhost:8000`. Make sure:

1. The API server is running
2. CORS is properly configured (already done in the API)
3. No firewall is blocking the connection

### Production

For production deployment:

1. Update the `API_BASE_URL` in the frontend integration file
2. Configure proper CORS origins in the API
3. Use environment variables for the API URL

```typescript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

## Testing the Integration

1. **Start the API server**:
   ```bash
   cd api
   python main.py
   ```

2. **Start the frontend**:
   ```bash
   cd builder
   npm run dev
   ```

3. **Test the integration**:
   - Send a message in the chat
   - Verify the AI responds
   - Check that YAML files are updated
   - Test chat history functionality

## Troubleshooting

### Common Issues

1. **CORS Errors**: Make sure the API is running and CORS is configured
2. **Connection Refused**: Check if the API server is running on the correct port
3. **YAML Not Updating**: Check the browser console for errors
4. **Chat History Not Loading**: Verify the API endpoint is working

### Debug Steps

1. Check browser network tab for API requests
2. Verify API server logs for errors
3. Test API endpoints directly with curl or Postman
4. Check browser console for JavaScript errors

## Advanced Features

### Session Management

The API supports chat sessions. To implement session management:

```typescript
// Start a new chat
api.startNewChat();

// Load an existing chat
api.loadChatSession(chatId);
```

### Real-time Updates

For real-time updates, you could implement WebSocket connections or polling:

```typescript
// Poll for updates every 5 seconds
setInterval(async () => {
    if (currentChatId) {
        const yamlFiles = await api.getYamlFiles(currentChatId);
        setYamlFiles(yamlFiles);
    }
}, 5000);
```

### Offline Support

Consider implementing offline support with local storage:

```typescript
// Save messages to local storage
localStorage.setItem('chat_messages', JSON.stringify(messages));

// Load messages from local storage
const savedMessages = localStorage.getItem('chat_messages');
if (savedMessages) {
    setMessages(JSON.parse(savedMessages));
}
```

## Next Steps

1. **Add Authentication**: Implement user authentication for the API
2. **Database Storage**: Replace file-based storage with a database
3. **Real-time Features**: Add WebSocket support for real-time updates
4. **Advanced AI**: Integrate with more sophisticated AI models
5. **YAML Validation**: Add client-side YAML validation
6. **Export Features**: Add ability to export generated YAML files 