const API_BASE_URL = 'http://localhost:8000'

export interface ChatMessage {
  content: string
  role: string
}

export interface ChatResponse {
  response: string
  yaml_files: Array<{
    name: string
    content: string
  }>
  chat_id: string
}

export interface YamlFile {
  name: string
  content: string
  language: 'yaml'
}

export interface ChatSession {
  id: string
  name: string
  created_at: string
  updated_at: string
  message_count: number
  messages: Array<{
    id: number
    role: string
    content: string
    timestamp: string
  }>
  yaml_files: Record<string, string>
}

export interface ChatHistory {
  id: string
  name: string
  created_at: string
  last_message: string
  message_count: number
}

class ApiService {
  private currentChatId: string | null = null

  async sendMessage(message: string, chatId?: string): Promise<ChatResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat_builder_agent`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: message,
          role: 'user',
          chat_id: chatId || this.currentChatId
        } as ChatMessage & { chat_id?: string })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: ChatResponse = await response.json()
      
      // Store the chat ID for future messages
      this.currentChatId = data.chat_id
      
      // Ensure YAML files have proper formatting
      data.yaml_files = data.yaml_files.map(file => ({
        ...file,
        content: this.formatYamlContent(file.content)
      }))
      
      return data
    } catch (error) {
      console.error('Error sending message:', error)
      // Return a fallback response if API is not available
      return this.getFallbackResponse(message)
    }
  }

  async getYamlFiles(chatId: string): Promise<YamlFile[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/get_yamls/${chatId}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      return data.map((file: any) => ({
        name: file.name,
        content: this.formatYamlContent(file.content),
        language: 'yaml' as const
      }))
    } catch (error) {
      console.error('Error fetching YAML files:', error)
      return []
    }
  }

  async getChatHistory(): Promise<ChatHistory[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat_history`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Error fetching chat history:', error)
      return []
    }
  }

  async getChatSession(chatId: string): Promise<ChatSession | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat_session/${chatId}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Error fetching chat session:', error)
      return null
    }
  }

  async createChatSession(name?: string): Promise<string> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat_sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      this.currentChatId = data.chat_id
      return data.chat_id
    } catch (error) {
      console.error('Error creating chat session:', error)
      throw error
    }
  }

  async deleteChatSession(chatId: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat_sessions/${chatId}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // If we're deleting the current chat, clear it
      if (this.currentChatId === chatId) {
        this.currentChatId = null
      }

      return true
    } catch (error) {
      console.error('Error deleting chat session:', error)
      return false
    }
  }

  async deleteAllChatSessions(): Promise<boolean> {
    try {
      console.log('API: Calling delete all chat sessions endpoint...')
      const response = await fetch(`${API_BASE_URL}/api/delete_all_chats`, {
        method: 'DELETE'
      })

      console.log('API: Delete all response status:', response.status)
      
      if (!response.ok) {
        console.error('API: Delete all failed with status:', response.status)
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      console.log('API: Delete all response:', result)

      // Clear current chat ID since all chats are deleted
      this.currentChatId = null

      return true
    } catch (error) {
      console.error('API: Error deleting all chat sessions:', error)
      return false
    }
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/health`)
      return response.ok
    } catch (error) {
      console.error('Health check failed:', error)
      return false
    }
  }

  getCurrentChatId(): string | null {
    return this.currentChatId
  }

  setCurrentChatId(chatId: string | null) {
    this.currentChatId = chatId
  }

  private formatYamlContent(content: string): string {
    // Remove any markdown code blocks if present
    let formatted = content.replace(/```yaml\n?|\n?```/g, '')
    
    // Ensure proper indentation and formatting
    formatted = formatted.trim()
    
    // Add a newline at the end if missing
    if (!formatted.endsWith('\n')) {
      formatted += '\n'
    }
    
    return formatted
  }

  private getFallbackResponse(message: string): ChatResponse {
    const messageLower = message.toLowerCase()
    
    let response = `I understand you want to: "${message}". I'll help you build the appropriate Maestro configuration.`
    let yamlFiles = []

    // Generate basic YAML based on keywords
    if (messageLower.includes('agent') || messageLower.includes('openai') || messageLower.includes('gpt')) {
      yamlFiles.push({
        name: 'agents.yaml',
        content: `# Agents configuration generated from conversation
agents:
  example_agent:
    type: openai
    config:
      model: gpt-4
      api_key: \${OPENAI_API_KEY}
      temperature: 0.7
    description: "Agent created based on: ${message}"
`
      })
    }

    if (messageLower.includes('workflow') || messageLower.includes('step') || messageLower.includes('process')) {
      yamlFiles.push({
        name: 'workflow.yaml',
        content: `# Workflow configuration generated from conversation
workflow:
  name: "Generated Workflow"
  description: "Workflow created based on: ${message}"
  steps:
    - name: "example_step"
      agent: "example_agent"
      input:
        prompt: "Process the request"
`
      })
    }

    // If no specific keywords, provide a general response
    if (yamlFiles.length === 0) {
      yamlFiles = [
        {
          name: 'agents.yaml',
          content: `# Agents configuration will be generated here
agents:
  # Your agents will appear here
  # Example:
  # example_agent:
  #   type: openai
  #   config:
  #     model: gpt-4
  #     api_key: \${OPENAI_API_KEY}
`
        },
        {
          name: 'workflow.yaml',
          content: `# Workflow configuration will be generated here
workflow:
  # Your workflow will appear here
  # Example:
  # name: "My Workflow"
  # steps:
  #   - name: "process_request"
  #     agent: "example_agent"
`
        }
      ]
    }

    return {
      response,
      yaml_files: yamlFiles,
      chat_id: 'fallback-session'
    }
  }
}

export const apiService = new ApiService() 