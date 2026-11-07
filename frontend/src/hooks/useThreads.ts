import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ChatMessage, ChatThread, ResponseType } from '../types'
import {
  createEmptyThread,
  loadThreadStore,
  saveThreadStore,
  titleFromMessages,
} from '../lib/threadStorage'

export function useThreads() {
  const [store, setStore] = useState(() => loadThreadStore())

  useEffect(() => {
    saveThreadStore(store)
  }, [store])

  const activeThread = useMemo(() => {
    return (
      store.threads.find((t) => t.id === store.activeId) ??
      store.threads[0] ??
      null
    )
  }, [store])

  const threadsSorted = useMemo(() => {
    return [...store.threads].sort((a, b) => b.updatedAt - a.updatedAt)
  }, [store.threads])

  const createThread = useCallback(() => {
    const thread = createEmptyThread()
    setStore((prev) => ({
      activeId: thread.id,
      threads: [thread, ...prev.threads],
    }))
    return thread
  }, [])

  const selectThread = useCallback((id: string) => {
    setStore((prev) => {
      if (!prev.threads.some((t) => t.id === id)) return prev
      return { ...prev, activeId: id }
    })
  }, [])

  const deleteThread = useCallback((id: string) => {
    setStore((prev) => {
      const remaining = prev.threads.filter((t) => t.id !== id)
      if (remaining.length === 0) {
        const thread = createEmptyThread()
        return { activeId: thread.id, threads: [thread] }
      }
      const activeId =
        prev.activeId === id
          ? [...remaining].sort((a, b) => b.updatedAt - a.updatedAt)[0].id
          : prev.activeId
      return { activeId, threads: remaining }
    })
  }, [])

  const updateActiveThread = useCallback(
    (patch: {
      messages?: ChatMessage[]
      responseType?: ResponseType
      title?: string
    }) => {
      setStore((prev) => {
        if (!prev.activeId) return prev
        return {
          ...prev,
          threads: prev.threads.map((t) => {
            if (t.id !== prev.activeId) return t
            const messages = patch.messages ?? t.messages
            const responseType = patch.responseType ?? t.responseType
            const title =
              patch.title ??
              (patch.messages ? titleFromMessages(messages) : t.title)
            return {
              ...t,
              messages,
              responseType,
              title,
              updatedAt: Date.now(),
            }
          }),
        }
      })
    },
    [],
  )

  return {
    threads: threadsSorted,
    activeThread: activeThread as ChatThread,
    createThread,
    selectThread,
    deleteThread,
    updateActiveThread,
  }
}
