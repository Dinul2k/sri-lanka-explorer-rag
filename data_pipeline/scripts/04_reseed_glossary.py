"""Re-embed glossary CSV into glossary_vectors without touching review_vectors."""
import os
import pandas as pd
import psycopg2
from pgvector.psycopg2 import register_vector
from InstructorEmbedding import INSTRUCTOR


def reseed_glossary():
    print("Connecting to PostgreSQL...")
    host = os.environ.get("POSTGRES_HOST", "127.0.0.1")
    default_port = "5432" if host not in ("localhost", "127.0.0.1") else "5433"
    port = os.environ.get("POSTGRES_PORT", default_port)
    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=os.environ.get("POSTGRES_DB", "tourism_db"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
    )
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    register_vector(conn)

    glossary_path = os.path.join(
        os.path.dirname(__file__), "..", "processed_data", "local_tourism_glossary.csv"
    )
    if not os.path.exists(glossary_path):
        raise SystemExit(f"Glossary file missing at {glossary_path}")

    df = pd.read_csv(glossary_path)
    print(f"Loaded {len(df)} glossary terms")

    print("Loading INSTRUCTOR model...")
    model = INSTRUCTOR("hkunlp/instructor-base")
    instruction = "Represent the Sri Lankan tourism query: "

    print("Recreating glossary_vectors...")
    cursor.execute(
        """
        DROP TABLE IF EXISTS glossary_vectors;
        CREATE TABLE glossary_vectors (
            id SERIAL PRIMARY KEY,
            term TEXT,
            translation TEXT,
            category TEXT,
            icon TEXT,
            embedding VECTOR(768)
        );
        """
    )

    print("Embedding and inserting glossary data...")
    for i, row in df.iterrows():
        term = row["term"]
        translation = row["english_translation"]
        text_to_embed = f"{term} - {translation}"
        embedding = model.encode([[instruction, text_to_embed]])[0]
        cursor.execute(
            """
            INSERT INTO glossary_vectors (term, translation, category, icon, embedding)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (term, translation, row["category"], row["icon"], embedding.tolist()),
        )
        if (i + 1) % 25 == 0 or (i + 1) == len(df):
            print(f"  {i + 1}/{len(df)}")

    cursor.close()
    conn.close()
    print("Glossary reseed completed.")


if __name__ == "__main__":
    reseed_glossary()
