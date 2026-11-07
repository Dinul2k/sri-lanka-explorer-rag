import { useEffect, useMemo, useState } from 'react'
import { fetchGlossary } from '../api/client'
import type { GlossaryTerm } from '../types'
import { SystemInfo } from './SystemInfo'

type Props = {
  onAskTerm?: (term: string) => void
  onBackToChat?: () => void
}

export function SlangView({ onAskTerm, onBackToChat }: Props) {
  const [terms, setTerms] = useState<GlossaryTerm[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [count, setCount] = useState(0)
  const [activeCategory, setActiveCategory] = useState('All')
  const [query, setQuery] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<GlossaryTerm | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    ;(async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await fetchGlossary(controller.signal)
        setTerms(data.terms)
        setCategories(data.categories)
        setCount(data.count)
      } catch (e) {
        if ((e as Error).name !== 'AbortError') {
          setError(e instanceof Error ? e.message : 'Failed to load slang glossary')
        }
      } finally {
        setLoading(false)
      }
    })()
    return () => controller.abort()
  }, [])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return terms.filter((t) => {
      const catOk = activeCategory === 'All' || t.category === activeCategory
      const qOk =
        !q ||
        t.term.toLowerCase().includes(q) ||
        t.translation.toLowerCase().includes(q)
      return catOk && qOk
    })
  }, [terms, activeCategory, query])

  return (
    <div className="slang-page">
      <div className="slang-page-inner">
        <header className="slang-page-header">
          <div>
            <h2>Research demo panel</h2>
            <p>
              Supported slang glossary · dual-DB retrieval · {count || '—'} indexed terms
            </p>
          </div>
          {onBackToChat && (
            <button type="button" className="slang-back-btn" onClick={onBackToChat}>
              ← Back to chat
            </button>
          )}
        </header>

        <SystemInfo variant="page" />

        <h3 className="slang-section-title">Supported slang</h3>

        <div className="slang-page-toolbar">
          <input
            className="slang-page-search"
            type="search"
            placeholder="Search slang terms or meanings…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Search slang terms"
          />
          <div className="slang-page-cats" role="tablist" aria-label="Slang categories">
            <button
              type="button"
              className={activeCategory === 'All' ? 'is-active' : undefined}
              onClick={() => setActiveCategory('All')}
            >
              All
            </button>
            {categories.map((c) => (
              <button
                key={c}
                type="button"
                className={activeCategory === c ? 'is-active' : undefined}
                onClick={() => setActiveCategory(c)}
              >
                {c}
              </button>
            ))}
          </div>
          <p className="slang-page-count">
            Showing {filtered.length} of {count}
          </p>
        </div>

        {loading && <p className="muted">Loading glossary…</p>}
        {error && <p className="error-text">{error}</p>}

        {!loading && !error && (
          <div className="slang-page-layout">
            <ul className="slang-page-list">
              {filtered.map((t) => (
                <li key={`${t.category}-${t.term}`}>
                  <button
                    type="button"
                    className={`slang-page-item ${selected?.term === t.term ? 'is-selected' : ''}`}
                    onClick={() => setSelected(t)}
                  >
                    <span className="slang-page-term">
                      {t.icon ? <span aria-hidden>{t.icon}</span> : null}
                      <strong>{t.term}</strong>
                    </span>
                    <span className="slang-page-cat">{t.category}</span>
                    <span className="slang-page-preview">{t.translation}</span>
                  </button>
                </li>
              ))}
            </ul>

            <aside className="slang-page-detail" aria-live="polite">
              {selected ? (
                <>
                  <p className="slang-page-detail-term">
                    {selected.icon ? `${selected.icon} ` : ''}
                    {selected.term}
                  </p>
                  <p className="slang-page-detail-cat">{selected.category}</p>
                  <p className="slang-page-detail-text">{selected.translation}</p>
                  {onAskTerm && (
                    <button
                      type="button"
                      className="slang-ask-btn"
                      onClick={() => onAskTerm(selected.term)}
                    >
                      Ask about “{selected.term}”
                    </button>
                  )}
                </>
              ) : (
                <p className="muted">Select a term to preview its meaning and ask the RAG bot.</p>
              )}
            </aside>
          </div>
        )}
      </div>
    </div>
  )
}
