# Performance tests (cache vs normal RAG)

Saved query bank + runner that measures the gap between:

| Path | Meaning | Expected `source` |
|---|---|---|
| **Normal / baseline** | First query in each family → Postgres retrieval + Ollama | `llama3_rag_fallback` |
| **Solution** | Later queries in the same family → Redis semantic cache | `cache` |

## Fixtures

```bash
python tests/generate_query_bank.py --count 1500
```

Writes `tests/fixtures/query_bank.json` (1000–2000 supported).

## Run benchmark

Requires the stack + Ollama healthy (`http://localhost:8001/info`).

```bash
# Full 1500-query run (flushes Redis, restarts FastAPI, then executes)
python tests/benchmark_cache_vs_rag.py --warmup

# Smoke subset
python tests/benchmark_cache_vs_rag.py --limit 30 --warmup
```

Results:

- `tests/results.md` — presentation deck with charts (from latest run)
- `tests/results/benchmark_<timestamp>.csv`
- `tests/results/benchmark_<timestamp>_summary.json`
- `tests/results/latest.csv` / `latest_summary.json`

**Note:** Unique family seeds call the LLM (slow). Repeats/paraphrases after a seed are intended cache hits (fast). A 1500-query run is dominated by ~100 seed LLM calls.
