import { useCallback, useEffect, useState } from 'react'
import './App.css'
import mermaid from 'mermaid'
import ReactMarkdown from 'react-markdown'
import { chatStream, health as healthApi, type StreamEvent, fetchDiagram } from './api'

type Message = {
  text: string
  type: 'user' | 'assistant'
  isError?: boolean
}

type TokenUsage = {
  promptTokens: number
  responseTokens: number
  totalTokens: number
}

function App() {
  const [prompt, setPrompt] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [health, setHealth] = useState<string>('unknown')
  const [diagramError, setDiagramError] = useState<string>('')
  const [isLoading, setIsLoading] = useState(false)
  const [lastUserPrompt, setLastUserPrompt] = useState('')
  const [tokenUsage, setTokenUsage] = useState<TokenUsage>({
    promptTokens: 0,
    responseTokens: 0,
    totalTokens: 0,
  })
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode')
    if (saved !== null) return saved === 'true'
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })
  const [leftPanelWidth, setLeftPanelWidth] = useState(() => {
    const saved = localStorage.getItem('leftPanelWidth')
    return saved ? parseFloat(saved) : 50
  })
  const [isDragging, setIsDragging] = useState(false)

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark-mode')
      document.body.style.backgroundColor = '#1a1a1a'
    } else {
      document.documentElement.classList.remove('dark-mode')
      document.body.style.backgroundColor = '#ffffff'
    }
    localStorage.setItem('darkMode', isDarkMode.toString())
  }, [isDarkMode])

  useEffect(() => {
    mermaid.initialize({ startOnLoad: false, securityLevel: 'loose', theme: isDarkMode ? 'dark' : 'default' })
  }, [isDarkMode])

  const checkHealth = useCallback(async () => {
    try {
      const status = await healthApi()
      setHealth(status)
    } catch (e) {
      setHealth('unreachable')
    }
  }, [])

  useEffect(() => {
    checkHealth()
  }, [])

  const executeStream = useCallback(async (userPrompt: string) => {
    setIsLoading(true)
    setLastUserPrompt(userPrompt)
    
    try {
      await chatStream(userPrompt, (data: StreamEvent) => {
        if (data.error) {
          setMessages((m) => [...m, { text: `Error: ${data.error}`, type: 'assistant', isError: true }])
          return
        }
        if (data.prompt_tokens !== undefined || data.response_tokens !== undefined || data.total_tokens !== undefined) {
          setTokenUsage((prev) => ({
            promptTokens: prev.promptTokens + (data.prompt_tokens || 0),
            responseTokens: prev.responseTokens + (data.response_tokens || 0),
            totalTokens: prev.totalTokens + (data.total_tokens || 0),
          }))
        }
        
        const line = data.step_name
          ? `${data.step_name} (${data.agent_name ?? ''}): ${data.step_result ?? ''}`
          : data.step_result ?? ''
        if (line) setMessages((m) => [...m, { text: line, type: 'assistant' }])
      })
    } catch (e: any) {
      setMessages((m) => [...m, { 
        text: `Stream failed: ${e?.message ?? e}`, 
        type: 'assistant',
        isError: true 
      }])
    } finally {
      setIsLoading(false)
    }
  }, [])

  const startStream = useCallback(async () => {
    if (!prompt.trim() || isLoading) return
    
    const userPrompt = prompt
    setMessages((m) => [...m, { text: userPrompt, type: 'user' }])
    setPrompt('')
    await executeStream(userPrompt)
  }, [prompt, isLoading, executeStream])

  const clearConversation = useCallback(() => {
    if (isLoading) return
    setMessages([])
    setLastUserPrompt('')
    setTokenUsage({ promptTokens: 0, responseTokens: 0, totalTokens: 0 })
  }, [isLoading])

  const retryLastMessage = useCallback(async () => {
    if (!lastUserPrompt || isLoading) return
    
    setMessages((m) => {
      for (let i = m.length - 1; i >= 0; i--) {
        if (m[i].type === 'user') return m.slice(0, i + 1)
      }
      return m
    })
    
    await executeStream(lastUserPrompt)
  }, [lastUserPrompt, isLoading, executeStream])

  const renderDiagram = useCallback(async () => {
    try {
      const data = await fetchDiagram()
      setDiagramError('')
      const container = document.getElementById('mermaid-diagram')
      if (!container) return
      try {
        mermaid.parse(data.diagram)
      } catch (err: any) {
        setDiagramError(err?.message || 'Invalid Mermaid diagram')
        container.innerHTML = ''
        return
      }
      const { svg } = await mermaid.render('workflowDiagram', data.diagram)
      container.innerHTML = svg
    } catch (e: any) {
      setDiagramError(e?.message || 'Failed to load diagram')
    }
  }, [])

  useEffect(() => {
    renderDiagram()
  }, [renderDiagram, isDarkMode])

  const handleMouseDown = useCallback(() => {
    setIsDragging(true)
  }, [])

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging) return
    const windowWidth = window.innerWidth
    const newLeftWidth = (e.clientX / windowWidth) * 100
    if (newLeftWidth >= 20 && newLeftWidth <= 80) {
      setLeftPanelWidth(newLeftWidth)
    }
  }, [isDragging])

  const handleMouseUp = useCallback(() => {
    if (isDragging) {
      setIsDragging(false)
      localStorage.setItem('leftPanelWidth', leftPanelWidth.toString())
    }
  }, [isDragging, leftPanelWidth])

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      return () => {
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isDragging, handleMouseMove, handleMouseUp])

  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      height: '100vh',
      backgroundColor: isDarkMode ? '#1a1a1a' : '#ffffff',
      color: isDarkMode ? '#fff' : '#000',
    }}>
      <div style={{ 
        padding: '16px 24px', 
        borderBottom: isDarkMode ? '1px solid #333' : '1px solid #ddd',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexShrink: 0,
      }}>
        <h2 style={{ margin: 0 }}>Maestro Workflow UI</h2>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <button
            onClick={() => setIsDarkMode(!isDarkMode)}
            style={{
              padding: '8px 12px',
              borderRadius: 8,
              border: isDarkMode ? '1px solid #444' : '1px solid #ddd',
              backgroundColor: 'transparent',
              color: isDarkMode ? '#fff' : '#666',
              fontSize: '18px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
            }}
            title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDarkMode ? '☀️' : '🌙'}
          </button>
          {messages.length > 0 && (
            <button
              onClick={clearConversation}
              disabled={isLoading}
              style={{
                padding: '8px 16px',
                borderRadius: 8,
                border: isDarkMode ? '1px solid #444' : '1px solid #ddd',
                backgroundColor: 'transparent',
                color: isDarkMode ? '#aaa' : '#666',
                fontSize: '14px',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                opacity: isLoading ? 0.5 : 1,
              }}
            >
              Clear Chat
            </button>
          )}
          {tokenUsage.totalTokens > 0 && (
            <div 
              style={{ 
                fontSize: '13px', 
                color: isDarkMode ? '#aaa' : '#666',
                padding: '6px 12px',
                borderRadius: 8,
                backgroundColor: isDarkMode ? '#2a2a2a' : '#f5f5f5',
                display: 'flex',
                gap: 8,
              }}
              title={`Prompt: ${tokenUsage.promptTokens.toLocaleString()} | Response: ${tokenUsage.responseTokens.toLocaleString()}`}
            >
              <span>🔢</span>
              <span>{tokenUsage.totalTokens.toLocaleString()} tokens</span>
            </div>
          )}
          <div style={{ fontSize: '14px', color: isDarkMode ? '#aaa' : '#666' }}>Health: {health}</div>
        </div>
      </div>

      <div style={{ 
        flex: 1,
        display: 'flex',
        overflow: 'hidden',
        userSelect: isDragging ? 'none' : 'auto',
      }}>
        <div style={{ 
          width: `${leftPanelWidth}%`,
          display: 'flex',
          flexDirection: 'column',
        }}>
          <div style={{ 
            flex: 1,
            overflowY: 'auto',
            padding: '24px',
            display: 'flex',
            flexDirection: 'column',
          }}>
            {messages.length === 0 && !isLoading ? (
              <div style={{ 
                flex: 1, 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                color: '#999',
                fontSize: '18px',
              }}>
                Start a conversation...
              </div>
            ) : (
              <>
                {messages.map((m, i) => {
                  const isLastMessage = i === messages.length - 1
                  const showRetry = isLastMessage && m.type === 'assistant' && !isLoading
                  
                  return (
                    <div key={i}>
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: m.type === 'user' ? 'flex-start' : 'flex-end',
                          marginBottom: 12,
                        }}
                      >
                        <div
                          className={`message-bubble ${m.type === 'user' ? 'user-message' : 'assistant-message'}`}
                          style={{
                            maxWidth: '70%',
                            padding: '10px 14px',
                            borderRadius: 18,
                            backgroundColor: m.isError 
                              ? '#ffebee' 
                              : m.type === 'user' ? '#007AFF' : '#E5E5EA',
                            color: m.isError 
                              ? '#c62828'
                              : m.type === 'user' ? 'white' : 'black',
                            textAlign: 'left',
                            border: m.isError ? '1px solid #ef5350' : 'none',
                          }}
                        >
                          <div className="markdown-content">
                            <ReactMarkdown>{m.text}</ReactMarkdown>
                          </div>
                        </div>
                      </div>
                      {showRetry && (
                        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 12, marginTop: -8 }}>
                          <button
                            onClick={retryLastMessage}
                            disabled={isLoading}
                            style={{
                              padding: '6px 12px',
                              borderRadius: 12,
                              border: '1px solid #ddd',
                              backgroundColor: 'white',
                              color: '#666',
                              fontSize: '13px',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              gap: 4,
                            }}
                            title="Regenerate response"
                          >
                            <span>🔄</span>
                            {m.isError ? 'Retry' : 'Regenerate'}
                          </button>
                        </div>
                      )}
                    </div>
                  )
                })}
                {isLoading && (
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'flex-end',
                      marginBottom: 12,
                    }}
                  >
                    <div
                      className="message-bubble assistant-message typing-indicator"
                      style={{
                        padding: '10px 14px',
                        borderRadius: 18,
                        backgroundColor: '#E5E5EA',
                        color: 'black',
                        display: 'flex',
                        gap: 4,
                        alignItems: 'center',
                      }}
                    >
                      <span className="dot"></span>
                      <span className="dot"></span>
                      <span className="dot"></span>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          <div style={{ 
            padding: '16px 24px',
            borderTop: isDarkMode ? '1px solid #333' : '1px solid #ddd',
            backgroundColor: isDarkMode ? '#1a1a1a' : '#ffffff',
            flexShrink: 0,
          }}>
            <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
              <textarea
                style={{ 
                  flex: 1, 
                  padding: '12px 16px',
                  borderRadius: 16,
                  border: isDarkMode ? '1px solid #444' : '1px solid #ddd',
                  fontSize: '15px',
                  outline: 'none',
                  resize: 'none',
                  minHeight: 48,
                  maxHeight: 200,
                  fontFamily: 'inherit',
                  lineHeight: '1.5',
                  opacity: isLoading ? 0.6 : 1,
                  backgroundColor: isDarkMode ? '#2a2a2a' : '#fff',
                  color: isDarkMode ? '#fff' : '#000',
                }}
                placeholder="Enter your prompt (Shift+Enter for new line)"
                value={prompt}
                disabled={isLoading}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    startStream()
                  }
                }}
                rows={1}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement
                  target.style.height = 'auto'
                  target.style.height = Math.min(target.scrollHeight, 200) + 'px'
                }}
              />
              <button 
                onClick={startStream}
                disabled={isLoading || !prompt.trim()}
                style={{
                  padding: '12px 24px',
                  borderRadius: 24,
                  border: 'none',
                  backgroundColor: isLoading || !prompt.trim() ? '#ccc' : '#007AFF',
                  color: 'white',
                  fontSize: '15px',
                  fontWeight: '500',
                  cursor: isLoading || !prompt.trim() ? 'not-allowed' : 'pointer',
                  opacity: isLoading || !prompt.trim() ? 0.6 : 1,
                  transition: 'all 0.2s ease',
                }}
              >
                {isLoading ? 'Sending...' : 'Send'}
              </button>
            </div>
          </div>
        </div>

        <div
          onMouseDown={handleMouseDown}
          style={{
            width: 6,
            cursor: 'col-resize',
            backgroundColor: isDarkMode ? '#333' : '#ddd',
            flexShrink: 0,
            position: 'relative',
            transition: isDragging ? 'none' : 'background-color 0.2s ease',
          }}
          onMouseEnter={(e) => {
            if (!isDragging) {
              e.currentTarget.style.backgroundColor = isDarkMode ? '#555' : '#bbb'
            }
          }}
          onMouseLeave={(e) => {
            if (!isDragging) {
              e.currentTarget.style.backgroundColor = isDarkMode ? '#333' : '#ddd'
            }
          }}
        />

        <div style={{ 
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: isDarkMode ? '#0f0f0f' : '#f9f9f9',
          overflow: 'hidden',
        }}>
          <div style={{ 
            padding: '16px 24px',
            borderBottom: isDarkMode ? '1px solid #333' : '1px solid #ddd',
            fontWeight: '500',
            fontSize: '16px',
          }}>
            Workflow Diagram
          </div>
          <div style={{ 
            flex: 1,
            overflowY: 'auto',
            padding: '24px',
          }}>
            {diagramError && (
              <div style={{ 
                color: 'crimson', 
                marginBottom: 16,
                padding: '12px',
                backgroundColor: isDarkMode ? '#2a0000' : '#ffebee',
                borderRadius: 8,
                border: '1px solid crimson',
              }}>
                Diagram error: {diagramError}
              </div>
            )}
            <div id="mermaid-diagram" style={{ minHeight: 120 }} />
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
