# 🌴 Sri Lanka Explorer — Geo-Partitioned RAG Tourism Chatbot

A fully offline, privacy-preserving AI tourism assistant for Sri Lanka. Built with a **Dual-Database RAG architecture** and a **Geo-Partitioned, Intent-Guarded Semantic Cache** to deliver instant, hallucination-free travel recommendations.

## 🚀 Key Features

- ⚡ **170× Faster Responses** via Redis Semantic Cache (168ms vs 28.6s)
- 📍 **Geo-Locked Retrieval** — Queries about Galle *only* retrieve Galle data
- 🛡️ **Critical Word Intent Guard** — Prevents "luxury" from matching "budget"
- 🧠 **Dual-Database RAG** — Separate vector tables for reviews (geo-filtered) and local slang (global)
- 🔒 **100% Offline** — No external APIs, runs entirely in Docker

## 🏗️ Architecture

```
User (Streamlit) → FastAPI → Redis Semantic Cache (Fast Path: <200ms)
                           ↓ (cache miss)
                    PostgreSQL pgvector
                    ├── review_vectors (geo-locked by district)
                    └── glossary_vectors (global slang: kottu, tuk-tuk, etc.)
                           ↓
                    Ollama (LLaMA 3.2:3b) → Augmented Response → Cache Write
```

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| API | FastAPI |
| Frontend | Streamlit |
| Embedding | `hkunlp/instructor-base` (768-dim) |
| LLM | LLaMA 3.2:3b via Ollama |
| Vector Cache | Redis Stack (FLAT index, Cosine) |
| Vector DB | PostgreSQL + pgvector |
| Container | Docker + docker-compose |

## ⚙️ Setup & Running

### Prerequisites
- Docker Desktop installed and running
- At least 8GB RAM available

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/Research_Project.git
cd Research_Project
```

### 2. Pull the LLaMA model
```bash
docker-compose up -d ollama_engine
docker exec tourism_ollama ollama pull llama3.2:3b
```

### 3. Start all services
```bash
docker-compose up -d
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

## 📁 Project Structure

```
Research_Project/
├── backend/            # FastAPI app + caching logic
│   └── main.py         # Core RAG + Hybrid Cache implementation
├── frontend/           # Streamlit UI
│   └── app.py
├── data_pipeline/
│   └── scripts/
│       ├── 01_generate_slang.py    # Local tourism glossary
│       ├── 02_clean_reviews.py     # Review cleaning pipeline
│       └── 03_seed_database.py     # DB seeding with embeddings
├── docker-compose.yml  # Full stack orchestration
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
