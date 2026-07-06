import { useState, useRef, useCallback } from 'react'
import { sendChat } from '../api'

export function useChat() {
  const [messages, setMessages] = useState([
    { role: 'system', content: 'System initialized. Modules ready.' }
  ])
  const [sending, setSending] = useState(false)
  const controllerRef = useRef(null)

  const append = useCallback((msg) => {
    setMessages(prev => [...prev, msg])
  }, [])

  const send = useCallback(async (text) => {
    if (!text.trim() || sending) return
    append({ role: 'user', content: text })
    setSending(true)

    const controller = new AbortController()
    controllerRef.current = controller

    try {
      const data = await sendChat(text, controller.signal)
      append({
        role: 'assistant',
        content: data.error ? `⚠️ Error: ${data.error}` : data.response,
        meta: data.error ? null : {
          model: data.model_used,
          task: data.task_type,
          ctx: data.context_used || 0,
        }
      })
    } catch (e) {
      if (e.name === 'AbortError') {
        append({ role: 'assistant', content: '🛑 Raciocínio interrompido.' })
      } else {
        append({ role: 'assistant', content: `❌ Connection Error: ${e}` })
      }
    } finally {
      setSending(false)
      controllerRef.current = null
    }
  }, [sending, append])

  const stop = useCallback(() => {
    if (controllerRef.current) controllerRef.current.abort()
  }, [])

  return { messages, sending, send, stop }
}
