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
                base_threshold = 0.88 if target_district else 0.90
                
                if similarity > base_threshold:
                    cached_query = getattr(res.docs[0], "raw_query", None)
                    
                    if cached_query:
                        import re
                        
                        # --- Critical Word Override (Intent Safety Net) ---
                        # These words carry the core INTENT of a query.
                        # If one appears in the new query but NOT in the cached query (or vice versa),
                        # the two queries have different intents and must NOT share a cache entry.
                        critical_words = {
                            # Price/quality intent
                            "luxury", "budget", "cheap", "expensive", "affordable", "premium",
                            "free", "costly", "economical", "high-end",
                            # Activity intent
                            "surfing", "shopping", "hiking", "swimming", "cycling", "diving",
                            "fishing", "climbing", "snorkeling", "kayaking",
                            # Audience intent
                            "couples", "children", "kids", "family", "solo", "groups", "friends",
                            # Meal/time intent
                            "breakfast", "lunch", "dinner", "brunch", "nightlife", "morning", "evening",
                            # Stay type
                            "hotel", "hostel", "villa", "resort", "guesthouse", "camping",
                            # Vibe intent
                            "quiet", "party", "calm", "busy", "adventure", "romantic", "historical"
                        }

                        stopwords = {"a", "an", "the", "in", "on", "at", "to", "for", "of", "with",
                                     "is", "are", "am", "was", "were", "what", "can", "i", "do",
                                     "you", "my", "me", "how", "where", "tell", "suggest", "give",
                                     "recommend", "please", "some", "any", "best", "good", "great",
                                     "visit", "go", "find", "get", "see", "know", "about", "there",
                                     "thing", "things", "place", "places", "want", "need", "like"}

                        words1 = set(re.findall(r'\b\w+\b', request.query.lower())) - stopwords
                        words2 = set(re.findall(r'\b\w+\b', cached_query.lower())) - stopwords

                        # Check if any critical word appears in one query but not the other
                        critical_in_q1 = words1 & critical_words
                        critical_in_q2 = words2 & critical_words
                        critical_word_mismatch = critical_in_q1.symmetric_difference(critical_in_q2)

                        if critical_word_mismatch:
                            print(f"Critical word mismatch {critical_word_mismatch} -> Cache Reject!")
                            pass  # Force RAG fallback — intents are different

                        else:
                            # Permissive Jaccard check (0.30) for general rephrasing
                            jaccard = len(words1.intersection(words2)) / len(words1.union(words2)) if words1 and words2 else 0.0

                            if jaccard < 0.30 and similarity < 0.985:
                                print(f"Semantically similar ({similarity:.4f}) but Lexically too different ({jaccard:.4f}) -> Cache Reject!")
                                pass  # Force RAG fallback
                            else:
                                cache_type = "Geo-Locked" if target_district else "Generic Search"
                                print(f"Cache Hit! ({cache_type}) Similarity: {similarity:.4f}, Jaccard: {jaccard:.4f}")
                                return {
                                    "response": res.docs[0].response,
                                    "source": "cache",
                                    "latency_target": "< 200ms",
                                    "similarity": similarity
                                }
        except Exception as e:
            print(f"Redis cache search error: {e}")
            
    # 2. Slow Path (RAG Fallback)
    print("Cache Miss. Executing RAG fallback to PostgreSQL...")
    
    with pg_conn.cursor() as cursor:
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
Use the following local glossary and destination reviews to answer the user's query contextually.

{context_str}

User Query: {request.query}
"""

    # Send requested explicitly to simple Ollama text generation endpoint
    ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    try:
        resp = requests.post(f"{ollama_url}/api/generate", json={
            "model": "llama3.2:3b",
            "prompt": augmented_prompt,
            "stream": False
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
