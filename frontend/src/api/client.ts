import type { GlossaryResponse, QueryRequest, QueryResponse, SystemInfo } from '../types'

const API_BASE = (import.meta.env.VITE_API_BASE as string | undefined)?.replace(/\/$/, '') || '/api'

async function parseError(res: Response): Promise<never> {
  let detail = res.statusText
  try {
    const body = await res.json()
    detail = body.detail ?? JSON.stringify(body)
  } catch {
    // ignore
  }
  throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
}

export async function fetchSystemInfo(signal?: AbortSignal): Promise<SystemInfo> {
  const res = await fetch(`${API_BASE}/info`, { signal })
  if (!res.ok) await parseError(res)
  return res.json()
}

export async function postQuery(
  body: QueryRequest,
  signal?: AbortSignal,
): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  })
  if (!res.ok) await parseError(res)
  return res.json()
}

export async function fetchGlossary(signal?: AbortSignal): Promise<GlossaryResponse> {
  const res = await fetch(`${API_BASE}/glossary`, { signal })
  if (!res.ok) await parseError(res)
  return res.json()
}
