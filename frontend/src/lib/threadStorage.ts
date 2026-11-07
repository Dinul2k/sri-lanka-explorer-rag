import type { ChatThread } from '../types'

export const THREAD_STORAGE_KEY = 'sle-chat-threads-v1'

export type ThreadStore = {
  activeId: string | null
  threads: ChatThread[]
}

export function createEmptyThread(): ChatThread {
  const now = Date.now()
  return {
    id: `${now}-${Math.random().toString(36).slice(2, 8)}`,
    title: 'New chat',
    createdAt: now,
    updatedAt: now,
    responseType: 'short',
    messages: [],
  }
}

export function loadThreadStore(): ThreadStore {
  try {
    const raw = localStorage.getItem(THREAD_STORAGE_KEY)
    if (!raw) {
      const thread = createEmptyThread()
      return { activeId: thread.id, threads: [thread] }
    }
    const parsed = JSON.parse(raw) as ThreadStore
    if (!parsed || !Array.isArray(parsed.threads) || parsed.threads.length === 0) {
      const thread = createEmptyThread()
      return { activeId: thread.id, threads: [thread] }
    }
    const activeId =
      parsed.activeId && parsed.threads.some((t) => t.id === parsed.activeId)
        ? parsed.activeId
        : parsed.threads[0].id
    return { activeId, threads: parsed.threads }
  } catch {
    const thread = createEmptyThread()
    return { activeId: thread.id, threads: [thread] }
  }
}

export function saveThreadStore(store: ThreadStore) {
  try {
    localStorage.setItem(THREAD_STORAGE_KEY, JSON.stringify(store))
  } catch {
    // Quota or private mode — ignore persistence failures.
  }
}

export function titleFromMessages(messages: ChatThread['messages']): string {
  const firstUser = messages.find((m) => m.role === 'user')
  if (!firstUser) return 'New chat'
  const cleaned = firstUser.content.replace(/\s+/g, ' ').trim()
  return cleaned.length > 42 ? `${cleaned.slice(0, 42)}…` : cleaned
}
