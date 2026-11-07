import type { ThemeMode } from '../hooks/useTheme'
import type { ChatThread } from '../types'
import { ChatAvatar } from './ChatAvatar'

type Props = {
  open: boolean
  onClose: () => void
  onNewChat: () => void
  threads: ChatThread[]
  activeThreadId: string
  onSelectThread: (id: string) => void
  onDeleteThread: (id: string) => void
  theme: ThemeMode
  onToggleTheme: () => void
}

function formatThreadTime(ts: number) {
  const d = new Date(ts)
  const now = new Date()
  const sameDay =
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  if (sameDay) {
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
}

export function Sidebar({
  open,
  onClose,
  onNewChat,
  threads,
  activeThreadId,
  onSelectThread,
  onDeleteThread,
  theme,
  onToggleTheme,
}: Props) {
  return (
    <>
      <div
        className={`sidebar-backdrop ${open ? 'is-open' : ''}`}
        onClick={onClose}
        aria-hidden={!open}
      />
      <aside className={`sidebar ${open ? 'is-open' : ''}`} aria-label="Sidebar">
        <div className="sidebar-top">
          <button type="button" className="new-chat-btn" onClick={onNewChat}>
            <span aria-hidden>+</span> New chat
          </button>
          <button type="button" className="sidebar-close" onClick={onClose} aria-label="Close sidebar">
            ✕
          </button>
        </div>

        <div className="sidebar-brand">
          <p className="sidebar-brand-name">Sri Lanka Explorer</p>
          <p className="sidebar-brand-sub">Geo-aware tourism RAG</p>
        </div>

        <div className="sidebar-section sidebar-threads-section">
          <p className="sidebar-section-label">Chats</p>
          {threads.length === 0 ? (
            <p className="sidebar-hint">No chats yet. Start a new one.</p>
          ) : (
            <ul className="thread-list">
              {threads.map((thread) => (
                <li key={thread.id}>
                  <div
                    className={`thread-item ${thread.id === activeThreadId ? 'is-active' : ''}`}
                  >
                    <button
                      type="button"
                      className="thread-open"
                      onClick={() => onSelectThread(thread.id)}
                      title={thread.title}
                    >
                      <span className="thread-title">{thread.title}</span>
                      <span className="thread-meta">
                        {thread.messages.length === 0
                          ? formatThreadTime(thread.updatedAt)
                          : `${thread.messages.length} · ${formatThreadTime(thread.updatedAt)}`}
                      </span>
                    </button>
                    <button
                      type="button"
                      className="thread-delete"
                      aria-label={`Delete chat ${thread.title}`}
                      title="Delete"
                      onClick={(e) => {
                        e.stopPropagation()
                        onDeleteThread(thread.id)
                      }}
                    >
                      ✕
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="sidebar-footer">
          <p className="sidebar-hint">
            Threads are saved in this browser’s local storage. Open <strong>Slang</strong> for the glossary and system info.
          </p>
          <button
            type="button"
            className="theme-toggle"
            onClick={onToggleTheme}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            <span className="theme-toggle-label">
              <span className="theme-toggle-icon" aria-hidden>
                {theme === 'dark' ? '☾' : '☀'}
              </span>
              Appearance
            </span>
            <span className="theme-toggle-value">{theme === 'dark' ? 'Dark' : 'Light'}</span>
          </button>
          <div className="sidebar-user">
            <ChatAvatar role="user" size={36} className="sidebar-user-avatar" />
            <div className="sidebar-user-meta">
              <p className="sidebar-user-name">Travel Guest</p>
              <p className="sidebar-user-sub">Local explorer</p>
            </div>
          </div>
          <p className="sidebar-footnote">Answers from local reviews & slang · offline Ollama</p>
        </div>
      </aside>
    </>
  )
}
