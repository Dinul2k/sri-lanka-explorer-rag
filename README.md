# 🌴 Sri Lanka Explorer — Geo-Partitioned RAG Tourism Chatbot

A fully offline, privacy-preserving AI tourism assistant for Sri Lanka. Built with a **Dual-Database RAG architecture** and a **Geo-Partitioned, Intent-Guarded Semantic Cache** to deliver instant, hallucination-free travel recommendations.

## 🚀 Key Features

- ⚡ **170× Faster Responses** via Redis Semantic Cache (168ms vs 28.6s)
- 📍 **Geo-Locked Retrieval** — Queries about Galle *only* retrieve Galle data
- 🛡️ **Critical Word Intent Guard** — Prevents "luxury" from matching "budget"
- 🧠 **Dual-Database RAG** — Separate vector tables for reviews (geo-filtered) and local slang (global)
- 🔒 **100% Offline** — No external APIs; Docker for data services, optional host Ollama for the LLM
- ✍️ **Short / Long answers** — User-selectable response length with separate cache namespaces

## 🏗️ Architecture

```
User (React) → nginx /api → FastAPI → Redis Semantic Cache (Fast Path: <200ms)
                                   ↓ (cache miss)
                            PostgreSQL pgvector
                            ├── review_vectors (geo-locked by district)
                            └── glossary_vectors (global slang: kottu, tuk-tuk, etc.)
                                   ↓
                            Ollama (configurable model) → Augmented Response → Cache Write
```

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| API | FastAPI |
| Frontend | Vite + React + TypeScript (nginx) |
| Embedding | `hkunlp/instructor-base` (768-dim) |
| LLM | Ollama (default `llama3.1:8b`, configurable) |
| Vector Cache | Redis Stack (FLAT index, Cosine) |
| Vector DB | PostgreSQL + pgvector |
| Container | Docker + docker-compose |

## ⚙️ Setup & Running

### Prerequisites
- Docker Desktop installed and running
- **8GB RAM minimum** (tight on MacBook Air M2 8GB — use hybrid mode below)
- For hybrid mode: [Ollama](https://ollama.com) installed on the host

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/Research_Project.git
cd Research_Project
cp .env.example .env   # optional: set OLLAMA_MODEL etc.
```

### 2. Recommended: Hybrid mode (host Ollama)

Runs Redis, Postgres, API, and UI in Docker. **Ollama runs on the host** so the LLM can use GPU/Metal and avoid Docker Desktop’s RAM ceiling.

```bash
# On the host
ollama pull llama3.1:8b
# Ollama desktop app usually serves already; otherwise: ollama serve

# Stack (no in-container Ollama)
docker compose -f docker-compose.yml -f docker-compose.hybrid.yml up -d --build
```

If RAM is tight (e.g. MacBook Air 8GB swapping), fall back with `OLLAMA_MODEL=llama3.2:3b` in `.env`.

### 3. Alternative: Fully bundled Docker

```bash
# in .env: OLLAMA_URL=http://ollama_engine:11434
docker compose --profile bundled-ollama up -d --build
docker exec tourism_ollama ollama pull llama3.1:8b
```

### 4. Seed the database (first time only)
```bash
# Add your dataset CSVs to data_pipeline/raw_data/ first
cd data_pipeline/scripts
python 01_generate_slang.py
python 02_clean_reviews.py
python 03_seed_database.py
```

### 5. Open the chatbot
Navigate to **http://localhost:8501**

### Frontend local development (optional)
```bash
cd frontend
npm install
npm run dev
```
Vite proxies `/api` → `http://localhost:8001` (FastAPI must already be running).

## 🧠 Model upgrades (8GB Mac)

Set `OLLAMA_MODEL` in `.env` (or export it) after `ollama pull <name>`:

| Step | Model | When to use |
|---|---|---|
| 1 (default) | `llama3.1:8b` | Better quality; prefer hybrid host Ollama |
| 2 | `llama3.2:3b` | Fallback if the machine swaps under load |

Env knobs (see `.env.example`):

| Variable | Default | Notes |
|---|---|---|
| `OLLAMA_MODEL` | `llama3.1:8b` | Any tag already pulled in Ollama |
| `OLLAMA_KEEP_ALIVE` | `5m` | Use `-1` to pin in RAM (faster, more pressure) |
| `OLLAMA_NUM_THREAD` | `4` | M2 performance cores |
| `OLLAMA_NUM_PREDICT` | `75` | Short answers → lower latency |
| `OLLAMA_NUM_PREDICT_LONG` | `320` | Long answers |
| `OLLAMA_TEMPERATURE` | `0.6` | Generation randomness |

**Check for swap** while generating. If the machine is swapping, drop back to 3B — a thrashing 8B is slower and worse than a stable 3B plus the semantic cache.

## 📁 Project Structure

```
Research_Project/
├── backend/                 # FastAPI app + caching logic
│   └── main.py
├── frontend/                # Vite React TypeScript UI
│   ├── src/
│   ├── Dockerfile           # multi-stage node build → nginx
│   └── nginx.conf           # SPA + /api proxy to FastAPI
├── data_pipeline/
│   └── scripts/
├── docker-compose.yml
├── docker-compose.hybrid.yml
├── .env.example
└── README.md
```

## 📊 Research Results

| Metric | Before Cache | After Cache |
|---|---|---|
| Response Latency | 28.6 seconds | **168 ms** |
| Speedup | 1× | **170.2×** |
| Cross-City Collision | 38.4% | **0.0%** |
| Opposite-Intent Collision | 45.2% | **0.0%** |
| Cache Hit Rate (Rephrases) | 0% | **94.2%** |
| Cache Precision | N/A | **98.5%** |

## 📝 Research Paper

This project is the implementation artifact for a research paper on:
> *"Geo-Partitioned, Intent-Guarded Semantic Caching for Domain-Specific RAG in Localized Tourism Applications"*

---
Built with ❤️ for Sri Lanka 🇱🇰
