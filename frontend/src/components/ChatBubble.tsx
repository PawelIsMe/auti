import type { ChatMessage } from '../types'

export function ChatBubble({ message }: { message: ChatMessage }) {
  return <div className={`message-row ${message.role}`}>
    {message.role === 'assistant' && <span className="bot-avatar">A</span>}
    <div className="message-content"><div className="bubble">{message.content}{message.imageUrl && <a className="chat-image-link" href={message.imageUrl} target="_blank" rel="noreferrer"><img className="chat-image" src={message.imageUrl} alt="Zdjęcie z kamery" onLoad={(event)=>{const pane=event.currentTarget.closest('.chat-scroll');pane?.scrollTo({top:pane.scrollHeight,behavior:'smooth'})}}/><span>Otwórz zdjęcie ↗</span></a>}</div><time>{message.time.toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })}</time></div>
    {message.role === 'user' && <span className="user-avatar">Ty</span>}
  </div>
}
