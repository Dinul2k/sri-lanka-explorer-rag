import { useState } from 'react'
import { Chat } from './components/Chat'
import { Sidebar } from './components/Sidebar'
import { useTheme } from './hooks/useTheme'
import { useThreads } from './hooks/useThreads'

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [seedQuery, setSeedQuery] = useState<string | undefined>(undefined)
  const [view, setView] = useState<'chat' | 'slang'>('chat')
  const { theme, toggleTheme } = useTheme()
  const {
    threads,
    activeThread,
    createThread,
    selectThread,
    deleteThread,
    updateActiveThread,
  } = useThreads()

  function startNewChat() {
    setSeedQuery(undefined)
    setView('chat')
    createThread()
    setSidebarOpen(false)
  }

  function openThread(id: string) {
    setSeedQuery(undefined)
    setView('chat')
    selectThread(id)
    setSidebarOpen(false)
  }

  function askAboutTerm(term: string) {
    createThread()
    setSeedQuery(`What does "${term}" mean for travellers in Sri Lanka?`)
    setView('chat')
  }

  return (
    <div className="app-shell">
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onNewChat={startNewChat}
        threads={threads}
        activeThreadId={activeThread.id}
        onSelectThread={openThread}
        onDeleteThread={deleteThread}
        theme={theme}
        onToggleTheme={toggleTheme}
      />
      <Chat
        key={activeThread.id}
        thread={activeThread}
        onThreadChange={updateActiveThread}
        view={view}
        onViewChange={setView}
        onOpenSidebar={() => setSidebarOpen(true)}
        seedQuery={seedQuery}
        onAskTerm={askAboutTerm}
      />
    </div>
  )
}
