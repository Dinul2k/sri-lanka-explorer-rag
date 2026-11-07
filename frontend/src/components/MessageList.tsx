import type { ChatMessage } from '../types'
import { ChatAvatar } from './ChatAvatar'

type Props = {
  messages: ChatMessage[]
  onSuggestion?: (text: string) => void
}

const SUGGESTIONS = [
  'Best budget food in Galle',
  'Tuk-tuk tips for Colombo',
  'What to know about Matale spice gardens',
  'Quiet beaches near Matara',
]

function messageTimestamp(m: ChatMessage): number | null {
  if (typeof m.createdAt === 'number') return m.createdAt
  const fromId = Number(String(m.id).split('-')[0])
  return Number.isFinite(fromId) && fromId > 0 ? fromId : null
}

function formatBubbleTime(ts: number) {
  const d = new Date(ts)
  const now = new Date()
  const sameDay =
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  const time = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  if (sameDay) return time
  const date = d.toLocaleDateString([], { month: 'short', day: 'numeric' })
  return `${date} · ${time}`
}

export function MessageList({ messages, onSuggestion }: Props) {
  if (messages.length === 0) {
    return (
      <div className="empty-chat">
        <div className="empty-logo" aria-hidden>
          <ChatAvatar role="assistant" size={52} />
        </div>
        <h2>How can I help you explore Sri Lanka?</h2>
        <p>Ask about food, beaches, temples, transport, or a district.</p>
        <div className="suggestion-grid">
          {SUGGESTIONS.map((s) => (
            <button key={s} type="button" className="suggestion-chip" onClick={() => onSuggestion?.(s)}>
              {s}
            </button>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="message-list" aria-live="polite">
      {messages.map((m) => {
        const ts = messageTimestamp(m)
        return (
          <article key={m.id} className={`msg-row msg-${m.role}`}>
            <div className="msg-avatar">
              <ChatAvatar role={m.role} size={34} />
            </div>
            <div className="msg-body">
              <div className="msg-heading">
                <div className="msg-role">{m.role === 'assistant' ? 'Sri Lanka Explorer' : 'You'}</div>
                {ts && (
                  <time className="msg-time" dateTime={new Date(ts).toISOString()}>
                    {formatBubbleTime(ts)}
                  </time>
                )}
              </div>
              <div className={`msg-bubble msg-bubble-${m.role}`}>
                <p>{m.content}</p>
              </div>
              {m.role === 'assistant' && (
                <footer className="msg-meta">
                  {m.source && (
                    <span className={`badge ${m.source === 'cache' ? 'badge-cache' : 'badge-rag'}`}>
                      {m.source}
                    </span>
                  )}
                  {m.responseType && <span>{m.responseType}</span>}
                  {typeof m.latencySec === 'number' && <span>{m.latencySec.toFixed(2)}s</span>}
                  {m.model && <span>{m.model}</span>}
                </footer>
              )}
            </div>
          </article>
        )
      })}
    </div>
  )
}
