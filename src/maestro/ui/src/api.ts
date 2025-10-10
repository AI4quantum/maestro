export type WorkflowChatResponse = {
  response: string
  workflow_name: string
  timestamp: string
}

export type StreamEvent = {
  step_name?: string
  step_result?: string
  agent_name?: string
  step_complete?: boolean
  error?: string
  prompt_tokens?: number
  response_tokens?: number
  total_tokens?: number
}

export async function health(): Promise<string> {
  const res = await fetch('/health')
  if (!res.ok) throw new Error('health failed')
  const j = await res.json()
  return j.status as string
}

export async function chat(prompt: string): Promise<WorkflowChatResponse> {
  const res = await fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, stream: false }),
  })
  if (!res.ok) throw new Error(`chat failed: ${res.status}`)
  return res.json()
}

export async function chatStream(
  prompt: string,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  const res = await fetch('/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt }),
  })
  if (!res.ok || !res.body) {
    throw new Error(`stream failed: ${res.status}`)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() || ''
    for (const chunk of parts) {
      const line = chunk.trim()
      if (!line) continue
      // Expect lines like: data: {json}\n\n
      const idx = line.indexOf('data:')
      const jsonPart = idx >= 0 ? line.slice(idx + 5).trim() : line
      try {
        const evt = JSON.parse(jsonPart) as StreamEvent
        onEvent(evt)
      } catch {
        // ignore malformed
      }
    }
  }
}

export async function fetchDiagram(): Promise<{ diagram: string; workflow_name: string }> {
  const res = await fetch('/diagram')
  if (!res.ok) throw new Error('diagram failed')
  return res.json()
}


