import os
import uuid
import numpy as np
import requests
from typing import Literal
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import psycopg2
from pgvector.psycopg2 import register_vector
import redis
from redis.commands.search.field import VectorField, TextField, TagField
from redis.commands.search.query import Query
from redis.commands.search.index_definition import IndexDefinition, IndexType
from InstructorEmbedding import INSTRUCTOR

app = FastAPI(title="Tourism RAG Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize models and connections globally
model = None
r = None
pg_conn = None

# Ollama / LLM knobs (override via env — useful on 8GB Apple Silicon)
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
# -1 = keep forever (faster repeats, more RAM). Prefer "5m" / "10m" on 8GB machines.
OLLAMA_KEEP_ALIVE = os.environ.get("OLLAMA_KEEP_ALIVE", "5m")
OLLAMA_NUM_THREAD = int(os.environ.get("OLLAMA_NUM_THREAD", "4"))
OLLAMA_NUM_PREDICT = int(os.environ.get("OLLAMA_NUM_PREDICT", "75"))
OLLAMA_NUM_PREDICT_LONG = int(os.environ.get("OLLAMA_NUM_PREDICT_LONG", "320"))
OLLAMA_TEMPERATURE = float(os.environ.get("OLLAMA_TEMPERATURE", "0.6"))
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "hkunlp/instructor-base")
EMBEDDING_DIM = 768
CACHE_ENABLED = os.environ.get("ENABLE_CACHE", "true").lower() == "true"

RESPONSE_PROMPTS = {
    "short": "Give a concise, direct answer in 2 to 3 sentences.",
    "long": (
        "Give a helpful, detailed answer (about 2 to 4 short paragraphs). "
        "Include practical tips, what to expect, and any relevant local terms from the glossary."
    ),
}

@app.on_event("startup")
def startup_event():
    global model, r, pg_conn
    
    print(f"Loading embedding model ({EMBEDDING_MODEL})...")
    model = INSTRUCTOR(EMBEDDING_MODEL)
    
    print("Connecting to Redis...")
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
    r = redis.Redis.from_url(redis_url)
    
    # Create Redis index for semantic cache
    try:
        try:
            r.ft("cache_idx").dropindex()
        except redis.exceptions.ResponseError:
            pass
            
        schema = (
            VectorField("embedding", "FLAT", {"TYPE": "FLOAT32", "DIM": 768, "DISTANCE_METRIC": "COSINE"}),
            TextField("response"),
            TagField("district"),
            TagField("response_type"),
        )
        r.ft("cache_idx").create_index(schema, definition=IndexDefinition(prefix=["cache:"], index_type=IndexType.HASH))
        print("Redis index created successfully.")
    except redis.exceptions.ResponseError:
        print("Redis index already exists.")
        
    print("Connecting to PostgreSQL...")
    pg_conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        dbname=os.environ.get("POSTGRES_DB", "tourism_db"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "postgres")
    )
    pg_conn.autocommit = True
    with pg_conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    register_vector(pg_conn)

def get_pg_conn():
    """Return a live PostgreSQL connection, reconnecting if the connection dropped."""
    global pg_conn
    try:
        # Quick check to see if connection is still alive
        pg_conn.cursor().execute("SELECT 1")
    except Exception:
        print("PostgreSQL connection lost. Reconnecting...")
        pg_conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            port=os.environ.get("POSTGRES_PORT", "5432"),
            dbname=os.environ.get("POSTGRES_DB", "tourism_db"),
            user=os.environ.get("POSTGRES_USER", "postgres"),
            password=os.environ.get("POSTGRES_PASSWORD", "postgres")
        )
        pg_conn.autocommit = True
        register_vector(pg_conn)
        print("PostgreSQL reconnected successfully.")
    return pg_conn

class QueryRequest(BaseModel):
    query: str
    response_type: Literal["short", "long"] = Field(default="short")

@app.get("/glossary")
def list_glossary(category: str | None = None, q: str | None = None):
    """List supported local slang / tourism glossary terms for the research demo UI."""
    try:
        with get_pg_conn().cursor() as cur:
            sql = "SELECT term, translation, category, icon FROM glossary_vectors"
            clauses = []
            params: list = []
            if category:
                clauses.append("LOWER(category) = LOWER(%s)")
                params.append(category)
            if q:
                clauses.append("(term ILIKE %s OR translation ILIKE %s)")
                params.extend([f"%{q}%", f"%{q}%"])
            if clauses:
                sql += " WHERE " + " AND ".join(clauses)
            sql += " ORDER BY category ASC, term ASC"
            cur.execute(sql, params)
            rows = cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Glossary lookup failed: {e}")

    terms = [
        {
            "term": term,
            "translation": translation,
            "category": category_name or "General",
            "icon": icon or "",
        }
        for term, translation, category_name, icon in rows
    ]
    categories = sorted({t["category"] for t in terms})
    return {
        "count": len(terms),
        "categories": categories,
        "terms": terms,
    }

@app.get("/info")
def system_info():
    """Runtime versions / config for the frontend system info panel."""
    redis_ok = False
    postgres_ok = False
    ollama_ok = False
    try:
        redis_ok = bool(r and r.ping())
    except Exception:
        pass
    try:
        with get_pg_conn().cursor() as cur:
            cur.execute("SELECT 1")
            postgres_ok = True
    except Exception:
        pass
    try:
        ollama_ok = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2).ok
    except Exception:
        pass

    return {
        "llm_model": OLLAMA_MODEL,
        "embedding_model": EMBEDDING_MODEL,
        "embedding_dimensions": EMBEDDING_DIM,
        "ollama_url": OLLAMA_URL,
        "ollama_keep_alive": OLLAMA_KEEP_ALIVE,
        "ollama_num_thread": OLLAMA_NUM_THREAD,
        "ollama_num_predict": OLLAMA_NUM_PREDICT,
        "ollama_num_predict_long": OLLAMA_NUM_PREDICT_LONG,
        "ollama_temperature": OLLAMA_TEMPERATURE,
        "response_types": ["short", "long"],
        "cache_enabled": CACHE_ENABLED,
        "vector_store": "PostgreSQL + pgvector",
        "semantic_cache": "Redis Stack (FLAT, cosine)",
        "status": {
            "redis": redis_ok,
            "postgres": postgres_ok,
            "ollama": ollama_ok,
            "embedding_loaded": model is not None,
        },
    }

def extract_district(query: str):
    """Scan query against hardcoded Sri Lankan districts."""
    districts = ["colombo", "gampaha", "galle", "matara", "badulla", "kalutara", "hatton", "rathnapura", "kurunegala", "matale", "hambantota"]
    query_lower = query.lower()
    for d in districts:
        if d in query_lower:
            return d
    return None

def update_cache(query_vector: list, response: str, target_district: str, request_query: str, response_type: str = "short"):
    """Asynchronously update Redis cache with new LLM response."""
    key = f"cache:{uuid.uuid4()}"
    vector_bytes = np.array(query_vector, dtype=np.float32).tobytes()
    r.hset(key, mapping={
        "embedding": vector_bytes,
        "response": response,
        "district": target_district if target_district else "none",
        "response_type": response_type,
        "raw_query": request_query,
    })
    print(f"Asynchronously updated Redis cache -> {key} (type={response_type})")

@app.post("/query")
def process_query(request: QueryRequest, background_tasks: BackgroundTasks):
    response_type = request.response_type
    num_predict = OLLAMA_NUM_PREDICT_LONG if response_type == "long" else OLLAMA_NUM_PREDICT
    review_limit = 5 if response_type == "long" else 3
    length_instruction = RESPONSE_PROMPTS[response_type]

    instruction = "Represent the Sri Lankan tourism query: "
    query_vector = model.encode([[instruction, request.query]])[0]
    
    target_district = extract_district(request.query)
    if target_district:
        print(f"Detected target district: {target_district}")
    print(f"Response type: {response_type} (num_predict={num_predict})")
    
    # 1. Fast Path (Cache Check) — scoped by district + response_type
    enable_cache = os.environ.get("ENABLE_CACHE", "true").lower() == "true"
    
    if enable_cache:
        vector_bytes = np.array(query_vector, dtype=np.float32).tobytes()
        
        filters = [f"@response_type:{{{response_type}}}"]
        if target_district:
            filters.append(f"@district:{{{target_district}}}")
        filter_clause = " ".join(filters)
        q_string = f"({filter_clause})=>[KNN 1 @embedding $vec AS score]"
            
        q = Query(q_string).return_fields("response", "score", "raw_query", "response_type").dialect(2)
        
        try:
            res = r.ft("cache_idx").search(q, {"vec": vector_bytes})
            if len(res.docs) > 0:
                distance = float(res.docs[0].score)
                similarity = 1 - distance
                
                # Dynamic Thresholds based on Geographic Safety
                base_threshold = 0.85 if target_district else 0.90
                
                if similarity > base_threshold:
                    cached_query = getattr(res.docs[0], "raw_query", None)
                    
                    if cached_query:
                        # --- Permanent Semantic Re-Ranking Guard ---
                        # Instead of brittle keyword/synonym word-lists that need constant
                        # manual maintenance, we use the already-loaded INSTRUCTOR model to
                        # re-embed the cached query and compute a DIRECT cosine similarity
                        # against the current query vector.
                        #
                        # This is language-agnostic: "hiking" vs "trekking", "animals" vs "wildlife",
                        # "cheap" vs "budget" — all handled automatically with ZERO manual updates.
                        #
                        # The geographic @district tag filter (above) handles location safety.
                        # This guard handles intent safety within the same geographic scope.
                        
                        instruction = "Represent the Sri Lankan tourism query: "
                        cached_vector = model.encode([[instruction, cached_query]])[0]
                        
                        # Direct cosine similarity between new query and cached query
                        dot = float(np.dot(query_vector, cached_vector))
                        norm = float(np.linalg.norm(query_vector) * np.linalg.norm(cached_vector))
                        semantic_similarity = dot / norm if norm > 0 else 0.0
                        
                        # Strict secondary threshold: true paraphrases score > 0.92
                        # Different-intent queries (beach vs waterfall) score < 0.88
                        secondary_threshold = 0.92
                        
                        if semantic_similarity >= secondary_threshold:
                            cache_type = "Geo-Locked" if target_district else "Generic Search"
                            print(f"Cache Hit! ({cache_type}/{response_type}) Redis sim: {similarity:.4f}, Semantic re-rank: {semantic_similarity:.4f}")
                            return {
                                "response": res.docs[0].response,
                                "source": "cache",
                                "latency_target": "< 200ms",
                                "similarity": semantic_similarity,
                                "response_type": response_type,
                            }
                        else:
                            print(f"Semantic re-rank rejected: {semantic_similarity:.4f} < {secondary_threshold} -> RAG Fallback")
        except Exception as e:
            print(f"Redis cache search error: {e}")
            
    # 2. Slow Path (RAG Fallback)
    print("Cache Miss. Executing RAG fallback to PostgreSQL...")
    
    with get_pg_conn().cursor() as cursor:
        # Retrieve relevant slang
        cursor.execute("""
            SELECT term, translation FROM glossary_vectors 
            ORDER BY embedding <=> %s::vector LIMIT 2
        """, (query_vector.tolist(),))
        glossary_results = cursor.fetchall()
        
        # Retrieve relevant reviews
        if target_district:
            cursor.execute("""
                SELECT district, review_context FROM review_vectors 
                WHERE LOWER(district) = %s
                ORDER BY embedding <=> %s::vector LIMIT %s
            """, (target_district, query_vector.tolist(), review_limit))
        else:
            cursor.execute("""
                SELECT district, review_context FROM review_vectors 
                ORDER BY embedding <=> %s::vector LIMIT %s
            """, (query_vector.tolist(), review_limit))
        review_results = cursor.fetchall()

    # Construct the augmented prompt
    context_str = "Local Tourism Glossary:\n"
    for term, trans in glossary_results:
        context_str += f"- {term}: {trans}\n"
        
    context_str += "\nRelevant Itinerary Reviews:\n"
    for district, rev in review_results:
        context_str += f"- {district}: {rev}\n"

    augmented_prompt = f"""You are a helpful travel assistant for Sri Lankan tourism.
Use the following local glossary and destination reviews to answer the user's query contextually. {length_instruction}

{context_str}

User Query: {request.query}
"""

    # Send request to Ollama text generation endpoint
    # keep_alive: parse numeric strings (e.g. "-1") so permanent pin still works when set
    keep_alive = OLLAMA_KEEP_ALIVE
    if isinstance(keep_alive, str) and keep_alive.lstrip("-").isdigit():
        keep_alive = int(keep_alive)

    try:
        resp = requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": OLLAMA_MODEL,
            "prompt": augmented_prompt,
            "stream": False,
            "keep_alive": keep_alive,
            "options": {
                # num_thread=4 targets Apple Silicon P-cores; raise on more cores if needed
                "num_thread": OLLAMA_NUM_THREAD,
                "num_predict": num_predict,
                "temperature": OLLAMA_TEMPERATURE,
            }
        }, timeout=600)
        resp.raise_for_status()
        llm_output = resp.json().get("response", "No explanation generated.")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ollama generation failed (model={OLLAMA_MODEL}): {str(e)}"
        )

    # 3. Asynchronously embed and Store the Response in Cache
    background_tasks.add_task(
        update_cache, query_vector, llm_output, target_district, request.query, response_type
    )

    return {
        "response": llm_output,
        "source": "llama3_rag_fallback",
        "model": OLLAMA_MODEL,
        "response_type": response_type,
        "context_used": {
            "glossary": glossary_results,
            "reviews": review_results
        }
    }
