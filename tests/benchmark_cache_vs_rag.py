"""
Run the saved query bank against the live /query API and compare:
  - baseline / normal path: first query in each family (RAG + Ollama)
  - solution path: later family queries (semantic cache)

Writes CSV + summary JSON under tests/results/.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_API = "http://localhost:8001"
FIXTURE = Path(__file__).parent / "fixtures" / "query_bank.json"
RESULTS_DIR = Path(__file__).parent / "results"


def http_json(method: str, url: str, body: dict | None = None, timeout: float = 600.0) -> dict:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post_query(api: str, query: str, response_type: str) -> tuple[dict, float]:
    started = time.perf_counter()
    payload = http_json(
        "POST",
        f"{api.rstrip('/')}/query",
        {"query": query, "response_type": response_type},
        timeout=600.0,
    )
    elapsed = time.perf_counter() - started
    return payload, elapsed


def flush_cache_and_reindex() -> None:
    """Clear Redis and restart FastAPI so the cache index is recreated empty."""
    log("Flushing Redis cache and restarting FastAPI for a clean baseline...")
    subprocess.run(
        ["docker", "exec", "tourism_redis", "redis-cli", "FLUSHDB"],
        check=False,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["docker", "restart", "tourism_fastapi"],
        check=False,
        capture_output=True,
        text=True,
    )
    # Wait until /info is healthy
    deadline = time.time() + 180
    while time.time() < deadline:
        try:
            info = http_json("GET", "http://localhost:8001/info", timeout=5)
            if info.get("status", {}).get("embedding_loaded"):
                log("API ready after restart.")
                return
        except Exception:
            time.sleep(2)
    raise RuntimeError("FastAPI did not become ready after cache flush")


def percentile(values: list[float], p: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    k = (len(ordered) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(ordered) - 1)
    if f == c:
        return ordered[f]
    return ordered[f] + (ordered[c] - ordered[f]) * (k - f)


def log(msg: str) -> None:
    print(msg, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default=DEFAULT_API)
    parser.add_argument("--fixture", type=Path, default=FIXTURE)
    parser.add_argument("--limit", type=int, default=0, help="Optional cap on cases (0 = all)")
    parser.add_argument("--skip-flush", action="store_true", help="Do not flush Redis before run")
    parser.add_argument("--warmup", action="store_true", help="Send one discard query to warm Ollama")
    parser.add_argument("--progress-every", type=int, default=25)
    args = parser.parse_args()

    if not args.fixture.exists():
        raise SystemExit(f"Missing fixture {args.fixture}. Run generate_query_bank.py first.")

    bank = json.loads(args.fixture.read_text(encoding="utf-8"))
    cases = bank["cases"]
    if args.limit and args.limit > 0:
        cases = cases[: args.limit]

    # Ensure /info works
    try:
        info = http_json("GET", f"{args.api.rstrip('/')}/info", timeout=10)
    except Exception as e:
        raise SystemExit(f"API not reachable at {args.api}: {e}") from e

    if not args.skip_flush:
        flush_cache_and_reindex()
        info = http_json("GET", f"{args.api.rstrip('/')}/info", timeout=30)

    if args.warmup:
        log("Warmup query (discarded from results)...")
        try:
            post_query(args.api, "Warmup query about Galle beaches", "short")
        except Exception as e:
            log(f"Warmup failed (continuing): {e}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw_path = RESULTS_DIR / f"benchmark_{stamp}.csv"
    summary_path = RESULTS_DIR / f"benchmark_{stamp}_summary.json"
    latest_raw = RESULTS_DIR / "latest.csv"
    latest_summary = RESULTS_DIR / "latest_summary.json"

    fieldnames = [
        "seq",
        "id",
        "family",
        "role",
        "district",
        "intent",
        "is_seed",
        "expect_source",
        "query",
        "response_type",
        "source",
        "latency_sec",
        "ok",
        "error",
        "source_match",
    ]

    rows: list[dict] = []
    family_seeded: set[str] = set()
    t0 = time.perf_counter()

    log(f"Running {len(cases)} queries against {args.api} ...")
    with raw_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()

        for i, case in enumerate(cases, start=1):
            family = case["family"]
            # First time we see a family in this run = baseline seed path
            is_seed_run = family not in family_seeded
            expect = "llama3_rag_fallback" if is_seed_run else "cache"
            ok = True
            err = ""
            source = ""
            latency = float("nan")
            try:
                payload, latency = post_query(args.api, case["query"], case.get("response_type", "short"))
                source = str(payload.get("source", ""))
                if is_seed_run:
                    family_seeded.add(family)
            except Exception as e:
                ok = False
                err = str(e)
                # still mark family seeded attempt to avoid infinite re-seed loops
                if is_seed_run:
                    family_seeded.add(family)

            row = {
                "seq": i,
                "id": case["id"],
                "family": family,
                "role": case.get("role", ""),
                "district": case.get("district", ""),
                "intent": case.get("intent", ""),
                "is_seed": is_seed_run,
                "expect_source": expect,
                "query": case["query"],
                "response_type": case.get("response_type", "short"),
                "source": source,
                "latency_sec": f"{latency:.4f}" if latency == latency else "",
                "ok": ok,
                "error": err,
                "source_match": bool(ok and source == expect),
            }
            rows.append(row)
            writer.writerow(row)
            fh.flush()

            if i % args.progress_every == 0 or i == len(cases):
                elapsed = time.perf_counter() - t0
                log(
                    f"  [{i}/{len(cases)}] last={source or 'ERR'} "
                    f"{latency:.2f}s · elapsed={elapsed/60:.1f}m · seeds={len(family_seeded)}"
                )

    baseline = [float(r["latency_sec"]) for r in rows if r["ok"] and r["source"] == "llama3_rag_fallback"]
    cached = [float(r["latency_sec"]) for r in rows if r["ok"] and r["source"] == "cache"]
    by_source = defaultdict(int)
    for r in rows:
        if r["ok"]:
            by_source[r["source"]] += 1
        else:
            by_source["error"] += 1

    matched = sum(1 for r in rows if r["source_match"])
    summary = {
        "created_at": stamp,
        "api": args.api,
        "model": info.get("llm_model"),
        "cache_enabled": info.get("cache_enabled"),
        "total_queries": len(rows),
        "ok": sum(1 for r in rows if r["ok"]),
        "errors": sum(1 for r in rows if not r["ok"]),
        "source_counts": dict(by_source),
        "expect_match_rate": matched / len(rows) if rows else 0.0,
        "baseline_rag": {
            "n": len(baseline),
            "mean_sec": statistics.mean(baseline) if baseline else None,
            "median_sec": statistics.median(baseline) if baseline else None,
            "p95_sec": percentile(baseline, 95) if baseline else None,
            "min_sec": min(baseline) if baseline else None,
            "max_sec": max(baseline) if baseline else None,
        },
        "solution_cache": {
            "n": len(cached),
            "mean_sec": statistics.mean(cached) if cached else None,
            "median_sec": statistics.median(cached) if cached else None,
            "p95_sec": percentile(cached, 95) if cached else None,
            "min_sec": min(cached) if cached else None,
            "max_sec": max(cached) if cached else None,
        },
        "speedup_mean": (
            (statistics.mean(baseline) / statistics.mean(cached))
            if baseline and cached and statistics.mean(cached) > 0
            else None
        ),
        "speedup_median": (
            (statistics.median(baseline) / statistics.median(cached))
            if baseline and cached and statistics.median(cached) > 0
            else None
        ),
        "wall_clock_sec": time.perf_counter() - t0,
        "raw_csv": str(raw_path.name),
    }

    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    latest_raw.write_text(raw_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    log("\n=== Benchmark summary ===")
    log(json.dumps(summary, indent=2))
    log(f"\nWrote {raw_path}")
    log(f"Wrote {summary_path}")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.URLError as e:
        print(f"HTTP error: {e}", file=sys.stderr)
        sys.exit(1)
