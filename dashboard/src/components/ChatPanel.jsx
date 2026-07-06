import { useState, useRef, useEffect } from 'react'
import { useChat } from '../hooks/useChat'
import Message from './Message'

function LoadingDots() {
  return (
    <div className="message loading">
      <div className="typing-dots">
        <span /><span /><span />
      </div>
    </div>
  )
}

export default function ChatPanel() {
  const { messages, sending, send, stop } = useChat()
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)
  const textRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  function autoResize() {
    const el = textRef.current
    if (!el) return
    el.style.height = '44px'
    el.style.height = Math.min(el.scrollHeight, 150) + 'px'
  }

  function handleSend() {
    if (!input.trim() || sending) return
    send(input)
    setInput('')
    if (textRef.current) {
      textRef.current.style.height = '44px'
    }
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <>
      <div className="chat-messages">
        {messages.map((msg, i) => (
          <Message key={i} msg={msg} />
        ))}
        {sending && <LoadingDots />}
        <div ref={bottomRef} />
      </div>
      <div className="input-area">
        <div className="input-wrapper">
          <textarea
            ref={textRef}
            value={input}
            onChange={e => { setInput(e.target.value); autoResize() }}
            onKeyDown={handleKey}
            placeholder="Digite sua mensagem..."
            rows={1}
            disabled={sending}
          />
        </div>
        {sending ? (
          <button className="btn btn-stop" onClick={stop}>Parar</button>
        ) : (
          <button className="btn btn-send" onClick={handleSend} disabled={!input.trim()}>
            Enviar
          </button>
        )}
      </div>
    </>
  )
}
