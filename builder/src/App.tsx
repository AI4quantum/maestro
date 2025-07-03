import { useState, useEffect } from 'react'
import { Sidebar } from './components/Sidebar'
import { ChatCanvas } from './components/ChatCanvas'
import { YamlPanel } from './components/YamlPanel'
import { ChatInput } from './components/ChatInput'
import { apiService, type ChatSession, type ChatHistory } from './services/api'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export interface YamlFile {
  name: string
  content: string
  language: 'yaml'
}

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m your Maestro AI Builder assistant. I can help you create agents.yaml and workflow.yaml files for your Maestro agents and workflows. What would you like to build today?',
      timestamp: new Date()
    }
  ])
  
  const [yamlFiles, setYamlFiles] = useState<YamlFile[]>([
    {
      name: 'agents.yaml',
      content: '# Agents configuration will be generated here\nagents:\n  # Your agents will appear here',
      language: 'yaml'
    },
    {
      name: 'workflow.yaml',
      content: '# Workflow configuration will be generated here\nworkflow:\n  # Your workflow will appear here',
      language: 'yaml'
    }
  ])

  const [isLoading, setIsLoading] = useState(false)
  const [currentChatId, setCurrentChatId] = useState<string | null>(null)
  const [chatHistory, setChatHistory] = useState<ChatHistory[]>([])

  // Load chat history on component mount
  useEffect(() => {
    loadChatHistory()
  }, [])

  const loadChatHistory = async () => {
    try {
      const history = await apiService.getChatHistory()
      setChatHistory(history)
    } catch (error) {
      console.error('Error loading chat history:', error)
    }
  }

  const loadChatSession = async (chatId: string) => {
    try {
      setIsLoading(true)
      const session = await apiService.getChatSession(chatId)
      
      if (session) {
        // Convert session messages to app format
        const sessionMessages: Message[] = session.messages.map(msg => ({
          id: msg.id.toString(),
          role: msg.role as 'user' | 'assistant',
          content: msg.content,
          timestamp: new Date(msg.timestamp)
        }))

        // Convert YAML files to app format, ensuring both files are always present
        const sessionYamlFiles: YamlFile[] = [
          {
            name: 'agents.yaml',
            content: session.yaml_files['agents.yaml'] || '# Agents configuration will be generated here\nagents:\n  # Your agents will appear here',
            language: 'yaml' as const
          },
          {
            name: 'workflow.yaml',
            content: session.yaml_files['workflow.yaml'] || '# Workflow configuration will be generated here\nworkflow:\n  # Your workflow will appear here',
            language: 'yaml' as const
          }
        ]

        setMessages(sessionMessages)
        setYamlFiles(sessionYamlFiles)
        setCurrentChatId(chatId)
        apiService.setCurrentChatId(chatId)
      }
    } catch (error) {
      console.error('Error loading chat session:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const createNewChat = async () => {
    try {
      const chatId = await apiService.createChatSession()
      setCurrentChatId(chatId)
      apiService.setCurrentChatId(chatId)
      
      // Reset to initial state with empty YAML files
      setMessages([
        {
          id: '1',
          role: 'assistant',
          content: 'Hello! I\'m your Maestro AI Builder assistant. I can help you create agents.yaml and workflow.yaml files for your Maestro agents and workflows. What would you like to build today?',
          timestamp: new Date()
        }
      ])
      
      // Set YAML files to empty state
      setYamlFiles([
        {
          name: 'agents.yaml',
          content: '# Agents configuration will be generated here\n# This file will contain your Maestro agent definitions\nagents:\n  # Your agents will appear here as you chat with the AI',
          language: 'yaml'
        },
        {
          name: 'workflow.yaml',
          content: '# Workflow configuration will be generated here\n# This file will contain your Maestro workflow definitions\nworkflow:\n  # Your workflow will appear here as you chat with the AI',
          language: 'yaml'
        }
      ])
      
      // Refresh chat history
      await loadChatHistory()
    } catch (error) {
      console.error('Error creating new chat:', error)
    }
  }

  const deleteChat = async (chatId: string) => {
    try {
      const success = await apiService.deleteChatSession(chatId)
      if (success) {
        // If we deleted the current chat, create a new one
        if (currentChatId === chatId) {
          await createNewChat()
        }
        // Refresh chat history
        await loadChatHistory()
      }
    } catch (error) {
      console.error('Error deleting chat:', error)
    }
  }

  const deleteAllChats = async () => {
    try {
      console.log('Starting delete all chats...')
      const success = await apiService.deleteAllChatSessions()
      console.log('Delete all chats result:', success)
      
      if (success) {
        console.log('Creating new chat after deletion...')
        // Create a new chat since all chats were deleted
        await createNewChat()
        console.log('Refreshing chat history...')
        // Refresh chat history (should be empty now)
        await loadChatHistory()
        console.log('Delete all chats completed successfully')
      } else {
        console.error('Failed to delete all chats - API returned false')
      }
    } catch (error) {
      console.error('Error deleting all chats:', error)
    }
  }

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    
    try {
      // Send message to API with current chat ID (pass undefined if null)
      const apiResponse = await apiService.sendMessage(content, currentChatId || undefined)
      
      // Create assistant message from API response
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: apiResponse.response,
        role: 'assistant',
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, assistantMessage])
      
      // Update YAML files from API response, merging with existing files
      const updatedYamlFiles = yamlFiles.map(file => {
        const apiFile = apiResponse.yaml_files.find(apiFile => apiFile.name === file.name)
        if (apiFile) {
          return {
            ...file,
            content: apiFile.content
          }
        }
        return file
      })
      
      setYamlFiles(updatedYamlFiles)
      
      // Update current chat ID if this is a new session
      if (apiResponse.chat_id !== currentChatId) {
        setCurrentChatId(apiResponse.chat_id)
        await loadChatHistory()
      }
      
    } catch (error) {
      console.error('Error sending message:', error)
      
      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error while processing your request. Please try again.',
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="h-screen flex bg-white overflow-hidden">
      {/* Left Sidebar */}
      <Sidebar 
        chatHistory={chatHistory}
        currentChatId={currentChatId}
        onLoadChat={loadChatSession}
        onCreateChat={createNewChat}
        onDeleteChat={deleteChat}
        onDeleteAllChats={deleteAllChats}
      />
      
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Chat Canvas */}
        <div className="flex-1 overflow-hidden">
          <ChatCanvas messages={messages} isLoading={isLoading} />
        </div>
        
        {/* Chat Input */}
        <div className="border-t border-gray-100 p-6">
          <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
        </div>
      </div>
      
      {/* Right Panel - YAML Files */}
      <YamlPanel yamlFiles={yamlFiles} isLoading={isLoading} />
    </div>
  )
}

export default App
