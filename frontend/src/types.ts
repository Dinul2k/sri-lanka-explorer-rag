export type ResponseType = 'short' | 'long'

export type QueryRequest = {
  query: string
  response_type?: ResponseType
}

export type QueryResponse = {
  response: string
  source: string
  model?: string
  response_type?: ResponseType
  latency_target?: string
  similarity?: number
  context_used?: {
    glossary?: [string, string][]
    reviews?: [string, string][]
  }
}

export type SystemInfo = {
  llm_model: string
  embedding_model: string
  embedding_dimensions: number
  ollama_url: string
  ollama_keep_alive: string
  ollama_num_thread: number
  ollama_num_predict: number
  ollama_num_predict_long?: number
  ollama_temperature: number
  response_types?: ResponseType[]
  cache_enabled: boolean
  vector_store: string
  semantic_cache: string
  status: {
    redis: boolean
    postgres: boolean
    ollama: boolean
    embedding_loaded: boolean
  }
}

export type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  createdAt?: number
  source?: string
  model?: string
  responseType?: ResponseType
  latencySec?: number
}

export type ChatThread = {
  id: string
  title: string
  createdAt: number
  updatedAt: number
  responseType: ResponseType
  messages: ChatMessage[]
}

export type GlossaryTerm = {
  term: string
  translation: string
  category: string
  icon?: string
}

export type GlossaryResponse = {
  count: number
  categories: string[]
  terms: GlossaryTerm[]
}
