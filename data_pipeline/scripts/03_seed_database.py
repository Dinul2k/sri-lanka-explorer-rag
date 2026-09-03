import os
import pandas as pd
import psycopg2
from pgvector.psycopg2 import register_vector
from InstructorEmbedding import INSTRUCTOR

def seed_db():
    print("Connecting to PostgreSQL...")
    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        dbname=os.environ.get("POSTGRES_DB", "tourism_db"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "postgres")
    )
    conn.autocommit = True
    cursor = conn.cursor()

    print("Enabling pgvector...")
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    register_vector(conn)

    # Note: Using 768 dimensions instead of 384 since INSTRUCTOR models output 768 dimensions inherently.
    print("Creating tables...")
    cursor.execute("""
        DROP TABLE IF EXISTS glossary_vectors;
        CREATE TABLE glossary_vectors (
            id SERIAL PRIMARY KEY,
            term TEXT,
            translation TEXT,
            category TEXT,
            icon TEXT,
            embedding VECTOR(768)
        );
    """)

    cursor.execute("""
        DROP TABLE IF EXISTS review_vectors;
        CREATE TABLE review_vectors (
            id SERIAL PRIMARY KEY,
            district TEXT,
            review_context TEXT,
            embedding VECTOR(768)
        );
    """)

    print("Loading INSTRUCTOR model...")
    # Initialize INSTRUCTOR model
    model = INSTRUCTOR('hkunlp/instructor-base')
    instruction = "Represent the Sri Lankan tourism query: "

    # Load and seed glossary
    glossary_path = os.path.join(os.path.dirname(__file__), "..", "processed_data", "local_tourism_glossary.csv")
    if os.path.exists(glossary_path):
        print("Embedding and inserting glossary data...")
        df_glossary = pd.read_csv(glossary_path)
        for _, row in df_glossary.iterrows():
            term = row['term']
            translation = row['english_translation']
            text_to_embed = f"{term} - {translation}"
            embedding = model.encode([[instruction, text_to_embed]])[0]
            
            cursor.execute("""
                INSERT INTO glossary_vectors (term, translation, category, icon, embedding)
                VALUES (%s, %s, %s, %s, %s)
            """, (term, translation, row['category'], row['icon'], embedding.tolist()))
    else:
        print(f"Glossary file missing at {glossary_path}")

    # Load and seed reviews
    reviews_path = os.path.join(os.path.dirname(__file__), "..", "processed_data", "cleaned_reviews.csv")
    if os.path.exists(reviews_path):
        print("Embedding and inserting review data...")
        df_reviews = pd.read_csv(reviews_path)
        for _, row in df_reviews.iterrows():
            context = row['review_context']
            embedding = model.encode([[instruction, context]])[0]
            
            cursor.execute("""
                INSERT INTO review_vectors (district, review_context, embedding)
                VALUES (%s, %s, %s)
            """, (row['district'], context, embedding.tolist()))
    else:
        print(f"Reviews file missing at {reviews_path}")

    print("Database seeding completed.")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    seed_db()
