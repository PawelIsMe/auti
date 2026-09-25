import { useEffect, useRef, useState, type FormEvent } from 'react'
import { api, ApiError } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { ChatBubble } from '../components/ChatBubble'
import { Button } from '../components/UI'

// randomUUID is only exposed in secure browser contexts. HTTP on a LAN is not
// considered secure by browsers, even though localhost is, so keep chat usable
// on a home network as well.
let fallbackId = 0
function createMessageId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  if (typeof crypto !== 'undefined' && typeof crypto.getRandomValues === 'function') {
    const bytes = crypto.getRandomValues(new Uint8Array(16))
    bytes[6] = (bytes[6] & 0x0f) | 0x40
    bytes[8] = (bytes[8] & 0x3f) | 0x80
    const hex = Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('')
    return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
  }
  fallbackId += 1
  return `message-${Date.now()}-${fallbackId}`
}

export function ChatView() {
  const { chatMessages: messages, addChatMessage } = useAuth()
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const chatScroll = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const pane = chatScroll.current
    if (pane) pane.scrollTo({ top: pane.scrollHeight, behavior: 'smooth' })
  }, [messages, busy])

  async function send(event: FormEvent) {
    event.preventDefault()
    const content = text.trim()
    if (!content || busy) return
    setText('')
    setError('')
    setBusy(true)
    addChatMessage({ id: createMessageId(), role: 'user', content, time: new Date() })
    try {
      const response = await api.chat(content)
      let imageUrl: string | undefined
      if (response.type === 'text/image' || response.img_url) {
        imageUrl = URL.createObjectURL(await api.snapshot(response.img_url))
      }
      addChatMessage({ id: createMessageId(), role: 'assistant', content: response.reply || '', time: new Date(), imageUrl })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Błąd połączenia.')
    } finally {
      setBusy(false)
    }
  }

  return <section className="chat-page">
    <div className="chat-scroll" ref={chatScroll}>
      {messages.length === 0
        ? <p className="chat-empty">Napisz wiadomość, aby rozpocząć rozmowę.</p>
        : <div className="message-list">{messages.map((message) => <ChatBubble key={message.id} message={message}/>)}{busy && <div className="typing-bubble"><i/><i/><i/></div>}<div/></div>}
      {error && <p className="chat-error">{error}</p>}
    </div>
    <form className="composer" onSubmit={send}>
      <div className="composer-box"><input aria-label="Wiadomość" value={text} onChange={(e)=>setText(e.target.value)} placeholder="Wiadomość…" disabled={busy}/></div>
      <Button type="submit" disabled={busy || !text.trim()} aria-label="Wyślij">↑</Button>
    </form>
  </section>
}
