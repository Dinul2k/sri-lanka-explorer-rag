import { useCallback, useEffect, useState } from 'react'
import { fetchSystemInfo } from '../api/client'
import type { SystemInfo as SystemInfoType } from '../types'

function StatusDot({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span className={`status-pill ${ok ? 'is-up' : 'is-down'}`}>
      <span className="status-dot" aria-hidden />
      {label}
    </span>
  )
}

type Props = {
  /** page = light full-width research panel; compact = collapsible card */
  variant?: 'page' | 'compact'
  defaultOpen?: boolean
}

export function SystemInfo({ variant = 'compact', defaultOpen = false }: Props) {
  const [open, setOpen] = useState(defaultOpen || variant === 'page')
  const [info, setInfo] = useState<SystemInfoType | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchSystemInfo()
      setInfo(data)
    } catch (e) {
      setInfo(null)
      setError(e instanceof Error ? e.message : 'Failed to load system info')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (open && !info && !loading) {
      void load()
    }
  }, [open, info, loading, load])

  if (variant === 'page') {
    return (
      <section className="sys-page-panel">
        <div className="sys-page-header">
          <div>
            <h3>System information</h3>
            <p>Runtime stack for the research demo</p>
          </div>
          <button type="button" className="ghost-btn ghost-btn-light" onClick={() => void load()}>
            Refresh
          </button>
        </div>
        {loading && <p className="muted">Loading…</p>}
        {error && <p className="error-text">{error}</p>}
        {info && (
          <>
            <dl className="sys-page-grid">
              <div>
                <dt>LLM model</dt>
                <dd>{info.llm_model}</dd>
              </div>
              <div>
                <dt>Embedding model</dt>
                <dd>
                  {info.embedding_model} ({info.embedding_dimensions}-dim)
                </dd>
              </div>
              <div>
                <dt>Vector store</dt>
                <dd>{info.vector_store}</dd>
              </div>
              <div>
                <dt>Semantic cache</dt>
                <dd>
                  {info.semantic_cache} · {info.cache_enabled ? 'enabled' : 'disabled'}
                </dd>
              </div>
              <div>
                <dt>Ollama endpoint</dt>
                <dd>
                  <code>{info.ollama_url}</code>
                </dd>
              </div>
              <div>
                <dt>Generation</dt>
                <dd>
                  temp={info.ollama_temperature}, short={info.ollama_num_predict}, long=
                  {info.ollama_num_predict_long ?? '—'}, threads={info.ollama_num_thread},
                  keep_alive={info.ollama_keep_alive}
                </dd>
              </div>
            </dl>
            <div className="sys-status-row sys-status-row-light">
              <StatusDot ok={info.status.redis} label="Redis" />
              <StatusDot ok={info.status.postgres} label="Postgres" />
              <StatusDot ok={info.status.ollama} label="Ollama" />
              <StatusDot ok={info.status.embedding_loaded} label="Embeddings" />
            </div>
          </>
        )}
      </section>
    )
  }

  return (
    <section className="sys-panel">
      <button
        type="button"
        className="sys-toggle"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        System information
        <span className="sys-chevron" aria-hidden>
          {open ? '▾' : '▸'}
        </span>
      </button>

      {open && (
        <div className="sys-body">
          {loading && <p className="muted">Loading…</p>}
          {error && <p className="error-text">{error}</p>}
          {info && (
            <>
              <dl className="sys-grid">
                <div>
                  <dt>LLM</dt>
                  <dd>{info.llm_model}</dd>
                </div>
                <div>
                  <dt>Embeddings</dt>
                  <dd>
                    {info.embedding_model} ({info.embedding_dimensions}-d)
                  </dd>
                </div>
                <div>
                  <dt>Vector store</dt>
                  <dd>{info.vector_store}</dd>
                </div>
                <div>
                  <dt>Cache</dt>
                  <dd>{info.cache_enabled ? 'on' : 'off'}</dd>
                </div>
                <div>
                  <dt>Ollama</dt>
                  <dd>
                    <code>{info.ollama_url}</code>
                  </dd>
                </div>
              </dl>
              <div className="sys-status-row">
                <StatusDot ok={info.status.redis} label="Redis" />
                <StatusDot ok={info.status.postgres} label="Postgres" />
                <StatusDot ok={info.status.ollama} label="Ollama" />
                <StatusDot ok={info.status.embedding_loaded} label="Embed" />
              </div>
              <button type="button" className="ghost-btn" onClick={() => void load()}>
                Refresh
              </button>
            </>
          )}
        </div>
      )}
    </section>
  )
}
