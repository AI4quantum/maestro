import { useCallback, useEffect, useState } from 'react'
import './App.css'
import mermaid from 'mermaid'
import ReactMarkdown from 'react-markdown'
import { chatStream, health as healthApi, type StreamEvent, fetchDiagram } from './api'

type Message = {
  text: string
  type: 'user' | 'assistant'
}

function App() {
  const [prompt, setPrompt] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [health, setHealth] = useState<string>('unknown')
  const [diagramError, setDiagramError] = useState<string>('')

  useEffect(() => {
    mermaid.initialize({ startOnLoad: false, securityLevel: 'loose', theme: 'default' })
  }, [])

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
  }, [checkHealth])

  const startStream = useCallback(async () => {
    if (!prompt.trim()) return
    setMessages((m) => [...m, { text: prompt, type: 'user' }])
    setPrompt('')
    try {
      await chatStream(prompt, (data: StreamEvent) => {
        if (data.error) {
          setMessages((m) => [...m, { text: `Error: ${data.error}`, type: 'assistant' }])
          return
        }
        const line = data.step_name
          ? `${data.step_name} (${data.agent_name ?? ''}): ${data.step_result ?? ''}`
          : data.step_result ?? ''
        if (line) setMessages((m) => [...m, { text: line, type: 'assistant' }])
      })
    } catch (e: any) {
      setMessages((m) => [...m, { text: `Stream failed: ${e?.message ?? e}`, type: 'assistant' }])
    }
  }, [prompt])

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
  }, [renderDiagram])

  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      height: '100vh',
      maxWidth: 1200,
      margin: '0 auto',
      backgroundColor: 'var(--bg-color, #ffffff)',
    }}>
      {/* Header */}
      <div style={{ 
        padding: '16px 24px', 
        borderBottom: '1px solid #ddd',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexShrink: 0,
      }}>
        <h2 style={{ margin: 0 }}>Maestro Workflow UI</h2>
        <div style={{ fontSize: '14px', color: '#666' }}>Health: {health}</div>
      </div>

      {/* Chat Messages Area */}
      <div style={{ 
        flex: 1,
        overflowY: 'auto',
        padding: '24px',
        display: 'flex',
        flexDirection: 'column',
      }}>
        {messages.length === 0 ? (
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
          messages.map((m, i) => (
            <div
              key={i}
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
                  backgroundColor: m.type === 'user' ? '#007AFF' : '#E5E5EA',
                  color: m.type === 'user' ? 'white' : 'black',
                  textAlign: 'left',
                }}
              >
                <div className="markdown-content">
                  <ReactMarkdown>{m.text}</ReactMarkdown>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Input Area - Fixed at bottom */}
      <div style={{ 
        padding: '16px 24px',
        borderTop: '1px solid #ddd',
        backgroundColor: 'var(--bg-color, #ffffff)',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', gap: 12, maxWidth: 1000, margin: '0 auto' }}>
          <input
            style={{ 
              flex: 1, 
              padding: '12px 16px',
              borderRadius: 24,
              border: '1px solid #ddd',
              fontSize: '15px',
              outline: 'none',
            }}
            placeholder="Enter your prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                startStream()
              }
            }}
          />
          <button 
            onClick={startStream}
            style={{
              padding: '12px 24px',
              borderRadius: 24,
              border: 'none',
              backgroundColor: '#007AFF',
              color: 'white',
              fontSize: '15px',
              fontWeight: '500',
              cursor: 'pointer',
            }}
          >
            Send
          </button>
        </div>
      </div>

      {/* Diagram Section - Collapsible */}
      <details style={{ 
        borderTop: '1px solid #ddd',
        backgroundColor: '#f9f9f9',
      }}>
        <summary style={{ 
          padding: '12px 24px',
          cursor: 'pointer',
          fontWeight: '500',
          userSelect: 'none',
        }}>
          Workflow Diagram
        </summary>
        <div style={{ padding: '16px 24px' }}>
          {diagramError && (
            <div style={{ color: 'crimson', marginBottom: 8 }}>Diagram error: {diagramError}</div>
          )}
          <div id="mermaid-diagram" style={{ minHeight: 120 }} />
        </div>
      </details>
    </div>
  )
}

export default App
