import { useEffect, useRef, useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'
import { postQuery } from '../api/client'
import type { ChatMessage, ChatThread, ResponseType } from '../types'
import { MessageList } from './MessageList'
import { ResponseLengthToggle } from './ResponseLengthToggle'
import { SlangView } from './SlangView'

function uid() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

type Props = {
  thread: ChatThread
  onThreadChange: (patch: {
    messages?: ChatMessage[]
    responseType?: ResponseType
  }) => void
  onOpenSidebar: () => void
  seedQuery?: string
  view: 'chat' | 'slang'
  onViewChange: (view: 'chat' | 'slang') => void
  onAskTerm?: (term: string) => void
}

export function Chat({
  thread,
  onThreadChange,
  onOpenSidebar,
  seedQuery,
  view,
  onViewChange,
  onAskTerm,
}: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>(thread.messages)
  const [input, setInput] = useState('')
  const [responseType, setResponseType] = useState<ResponseType>(thread.responseType)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const responseTypeRef = useRef(responseType)
  const seededRef = useRef(false)
  const skipPersistRef = useRef(true)

  useEffect(() => {
    responseTypeRef.current = responseType
  }, [responseType])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = '0px'
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`
  }, [input])

  useEffect(() => {
    if (skipPersistRef.current) {
      skipPersistRef.current = false
      return
    }
    onThreadChange({ messages, responseType })
  }, [messages, responseType, onThreadChange])

  async function send(query: string) {
    const trimmed = query.trim()
    if (!trimmed) return

    setError(null)
    setInput('')
    setMessages((prev) => [
      ...prev,
      { id: uid(), role: 'user', content: trimmed, createdAt: Date.now() },
    ])
    setLoading(true)

    const started = performance.now()
    try {
      const data = await postQuery({
        query: trimmed,
        response_type: responseTypeRef.current,
      })
      const latencySec = (performance.now() - started) / 1000
      setMessages((prev) => [
        ...prev,
        {
          id: uid(),
          role: 'assistant',
          content: data.response,
          createdAt: Date.now(),
          source: data.source,
          model: data.model,
          responseType: data.response_type ?? responseTypeRef.current,
          latencySec,
        },
      ])
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Could not reach the backend. It may still be starting up.',
      )
    } finally {
      setLoading(false)
      textareaRef.current?.focus()
    }
  }

  useEffect(() => {
    if (!seedQuery || seededRef.current) return
    seededRef.current = true
    void send(seedQuery)
  }, [seedQuery])

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    void send(input)
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void send(input)
    }
  }

  return (
    <div className="chat-main">
      <header className="chat-topbar">
        <button type="button" className="icon-btn" onClick={onOpenSidebar} aria-label="Open sidebar">
          ☰
        </button>
        <div className="topbar-title">
          <span className="topbar-brand">Sri Lanka Explorer</span>
          {view === 'chat' && (
            <ResponseLengthToggle
              value={responseType}
              onChange={setResponseType}
              disabled={loading}
            />
          )}
        </div>
        <button
          type="button"
          className={`topbar-slang-btn ${view === 'slang' ? 'is-active is-close' : ''}`}
          onClick={() => onViewChange(view === 'slang' ? 'chat' : 'slang')}
          aria-pressed={view === 'slang'}
          aria-label={view === 'slang' ? 'Close slang panel' : 'Open slang panel'}
          title={view === 'slang' ? 'Close' : 'Slang'}
        >
          {view === 'slang' ? (
            <span className="topbar-slang-close" aria-hidden>
              ✕
            </span>
          ) : (
            'Slang'
          )}
        </button>
      </header>

      {view === 'slang' ? (
        <SlangView
          onAskTerm={onAskTerm}
          onBackToChat={() => onViewChange('chat')}
        />
      ) : (
        <>
          <div className="chat-scroll">
            <div className="chat-column">
              <MessageList messages={messages} onSuggestion={(text) => void send(text)} />
              {loading && (
                <div className="thinking" role="status">
                  <span className="thinking-dot" />
                  Thinking…
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          </div>

          <div className="composer-dock">
            <div className="composer-column">
              {error && <p className="error-text">{error}</p>}
              <form className="composer" onSubmit={onSubmit}>
                <label className="sr-only" htmlFor="chat-input">
                  Your question
                </label>
                <textarea
                  id="chat-input"
                  ref={textareaRef}
                  rows={1}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={onKeyDown}
                  placeholder="Message Sri Lanka Explorer…"
                  disabled={loading}
                  autoComplete="off"
                />
                <button
                  type="submit"
                  className="send-btn"
                  disabled={loading || !input.trim()}
                  aria-label="Send message"
                >
                  ↑
                </button>
              </form>
              <p className="composer-hint">Enter to send · Shift+Enter for a new line · chats saved locally</p>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
