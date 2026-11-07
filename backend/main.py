import os
import uuid
import numpy as np
import requests
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import psycopg2
from pgvector.psycopg2 import register_vector
import redis
from redis.commands.search.field import VectorField, TextField, TagField
from redis.commands.search.query import Query
from redis.commands.search.index_definition import IndexDefinition, IndexType
from InstructorEmbedding import INSTRUCTOR

app = FastAPI(title="Tourism RAG Backend")

# Initialize models and connections globally
model = None
r = None
pg_conn = None

@app.on_event("startup")
def startup_event():
    global model, r, pg_conn
    
    print("Loading embedding model...")
    model = INSTRUCTOR('hkunlp/instructor-base')
    
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
            TagField("district")
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

def extract_district(query: str):
    """Scan query against hardcoded Sri Lankan districts."""
    districts = ["colombo", "gampaha", "galle", "matara", "badulla", "kalutara", "hatton", "rathnapura", "kurunegala", "matale", "hambantota"]
    query_lower = query.lower()
    for d in districts:
        if d in query_lower:
            return d
    return None

def update_cache(query_vector: list, response: str, target_district: str, request_query: str):
    """Asynchronously update Redis cache with new LLM response."""
    key = f"cache:{uuid.uuid4()}"
    vector_bytes = np.array(query_vector, dtype=np.float32).tobytes()
    r.hset(key, mapping={
        "embedding": vector_bytes,
        "response": response,
        "district": target_district if target_district else "none",
        "raw_query": request_query
    })
    print(f"Asynchronously updated Redis cache -> {key}")

@app.post("/query")
def process_query(request: QueryRequest, background_tasks: BackgroundTasks):
    instruction = "Represent the Sri Lankan tourism query: "
    query_vector = model.encode([[instruction, request.query]])[0]
    
    target_district = extract_district(request.query)
    if target_district:
        print(f"Detected target district: {target_district}")
    
    # 1. Fast Path (Cache Check)
    enable_cache = os.environ.get("ENABLE_CACHE", "true").lower() == "true"
    
    if enable_cache:
        vector_bytes = np.array(query_vector, dtype=np.float32).tobytes()
        
        if target_district:
            q_string = f"@district:{{{target_district}}}=>[KNN 1 @embedding $vec AS score]"
        else:
            q_string = "*=>[KNN 1 @embedding $vec AS score]"
            
        q = Query(q_string).return_fields("response", "score", "raw_query").dialect(2)
        
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
                            print(f"Cache Hit! ({cache_type}) Redis sim: {similarity:.4f}, Semantic re-rank: {semantic_similarity:.4f}")
                            return {
                                "response": res.docs[0].response,
                                "source": "cache",
                                "latency_target": "< 200ms",
                                "similarity": semantic_similarity
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
                ORDER BY embedding <=> %s::vector LIMIT 3
            """, (target_district, query_vector.tolist()))
        else:
            cursor.execute("""
                SELECT district, review_context FROM review_vectors 
                ORDER BY embedding <=> %s::vector LIMIT 3
            """, (query_vector.tolist(),))
        review_results = cursor.fetchall()

    # Construct the augmented prompt
    context_str = "Local Tourism Glossary:\n"
    for term, trans in glossary_results:
        context_str += f"- {term}: {trans}\n"
        
    context_str += "\nRelevant Itinerary Reviews:\n"
    for district, rev in review_results:
        context_str += f"- {district}: {rev}\n"

    augmented_prompt = f"""You are a helpful travel assistant for Sri Lankan tourism.
Use the following local glossary and destination reviews to answer the user's query contextually. Give a concise, direct answer in 2 to 3 sentences.

{context_str}

User Query: {request.query}
"""

    # Send requested explicitly to simple Ollama text generation endpoint
    ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    try:
        resp = requests.post(f"{ollama_url}/api/generate", json={
            "model": "llama3.2:3b",
            "prompt": augmented_prompt,
            "stream": False,
            "keep_alive": -1,  # Keep model permanently in memory — eliminates cold-start delay
            "options": {
                "num_thread": 4,     # Restrict to 4 Apple Silicon Performance cores (avoids slow E-core stalls)
                "num_predict": 75,   # Caps response to 2-3 sentences (~10-15s total latency)
                "temperature": 0.6
            }
        }, timeout=600)  # 10-minute timeout for CPU-based LLM inference
        resp.raise_for_status()
        llm_output = resp.json().get("response", "No explanation generated.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama generation failed: {str(e)}")
        
    # 3. Asynchronously embed and Store the Response in Cache
    background_tasks.add_task(update_cache, query_vector, llm_output, target_district, request.query)
    
    return {
        "response": llm_output,
        "source": "llama3_rag_fallback",
        "context_used": {
            "glossary": glossary_results,
            "reviews": review_results
        }
    }
