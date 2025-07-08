// Example integration code for the Maestro Builder frontend
// This shows how to use the API endpoints from the React frontend

const API_BASE_URL = 'http://localhost:5174';

interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

interface YamlFile {
    name: string;
    content: string;
}

interface ChatResponse {
    response: string;
    yaml_files: YamlFile[];
}

class MaestroBuilderAPI {
    private baseUrl: string;
    private currentChatId: string | null;

    constructor() {
        this.baseUrl = API_BASE_URL;
        this.currentChatId = null;
    }

    // Send a message to the chat builder agent
    async sendMessage(content: string): Promise<ChatResponse & { chatId: string }> {
        try {
            const payload: any = {
                content: content,
                role: 'user'
            };

            // Include chat_id if we have an ongoing conversation
            if (this.currentChatId) {
                payload.chat_id = this.currentChatId;
            }

            const response = await fetch(`${this.baseUrl}/api/chat_builder_agent`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Store the chat ID for future messages
            if (!this.currentChatId) {
                // Extract chat_id from response headers or response data
                // For now, we'll generate a new one
                this.currentChatId = this.generateChatId();
            }

            return {
                ...data,
                chatId: this.currentChatId
            };
        } catch (error) {
            console.error('Error sending message:', error);
            throw error;
        }
    }

    // Get YAML files for a specific chat session
    async getYamlFiles(chatId: string): Promise<YamlFile[]> {
        try {
            const response = await fetch(`${this.baseUrl}/api/get_yamls/${chatId}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error getting YAML files:', error);
            throw error;
        }
    }

    // Get chat history
    async getChatHistory(): Promise<any[]> {
        try {
            const response = await fetch(`${this.baseUrl}/api/chat_history`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error getting chat history:', error);
            throw error;
        }
    }

    // Load a specific chat session
    loadChatSession(chatId: string): void {
        this.currentChatId = chatId;
    }

    // Start a new chat session
    startNewChat(): void {
        this.currentChatId = null;
    }

    // Generate a simple chat ID (in production, this would come from the API)
    private generateChatId(): string {
        return 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
}

export default MaestroBuilderAPI;
export type { ChatMessage, YamlFile, ChatResponse }; 