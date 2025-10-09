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
    <div style={{ maxWidth: 900, margin: '0 auto', padding: 16 }}>
      <h2>Maestro Workflow UI</h2>
      <div style={{ marginBottom: 8 }}>Health: {health}</div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <input
          style={{ flex: 1, padding: 8 }}
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
        <button onClick={startStream}>Send</button>
      </div>

      <div style={{ border: '1px solid #ddd', padding: 16, minHeight: 160, overflowY: 'auto', maxHeight: 500 }}>
        {messages.map((m, i) => (
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
        ))}
      </div>

      <h4 style={{ marginTop: 16 }}>Workflow Diagram</h4>
      {diagramError && (
        <div style={{ color: 'crimson', marginBottom: 8 }}>Diagram error: {diagramError}</div>
      )}
      <div id="mermaid-diagram" style={{ minHeight: 120 }} />
    </div>
  )
}

export default App
