import pandas as pd
import psycopg2
from google import genai
from google.genai import types
from tqdm import tqdm
import os
import time
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# DB Credentials
DB_CONFIG = {
    "host": "localhost",
    "database": "motif_db",
    "user": "postgres",
    "password": "password"
}

def ingest_production():
    print("🔌 Connecting to Motif DB...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # 1. SETUP EXTENSIONS & SCHEMA
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    # Dropping old table to start fresh as requested
    cur.execute("DROP TABLE IF EXISTS movies CASCADE;")
    
    print("🛠️ Creating Production Schema (with Popularity Boost)...")
    cur.execute("""
        CREATE TABLE movies (
            id SERIAL PRIMARY KEY,
            tmdb_id INTEGER UNIQUE,
            title TEXT NOT NULL,
            overview TEXT,
            synthetic_vibe TEXT,
            poster_url TEXT,
            trailer_url TEXT,
            director TEXT,
            cast_members TEXT,
            writer TEXT,
            composer TEXT,
            runtime INTEGER,
            rating NUMERIC(3,1),
            popularity NUMERIC(12,3), -- Added Popularity Column
            release_year INTEGER,
            genres TEXT,
            tagline TEXT,
            embedding vector(768),
            -- Expanded search vector for hybrid keyword matching
            search_vector tsvector GENERATED ALWAYS AS (
                to_tsvector('english', coalesce(title, '')) || 
                to_tsvector('english', coalesce(genres, '')) || 
                to_tsvector('english', coalesce(director, '')) ||
                to_tsvector('english', coalesce(synthetic_vibe, ''))
            ) STORED
        );
    """)

    # 2. LOAD DATA
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_csv = os.path.join(script_dir, "../data/motif_final_rag.csv")
    
    if not os.path.exists(input_csv):
        print(f"❌ Error: {input_csv} not found.")
        return

    df = pd.read_csv(input_csv).fillna("")

    # 3. EMBED & INSERT
    print(f"🧠 Embedding {len(df)} movies...")
    for _, row in tqdm(df.iterrows(), total=len(df)):
        try:
            # Generate Gemini Embedding (Task: RETRIEVAL_DOCUMENT)
            res = client.models.embed_content(
                model="text-embedding-004",
                contents=row['rag_content'],
                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
            )
            vector = res.embeddings[0].values

            cur.execute("""
                INSERT INTO movies (
                    tmdb_id, title, overview, synthetic_vibe, poster_url, 
                    trailer_url, director, cast_members, writer, composer, 
                    runtime, rating, popularity, release_year, genres, tagline, embedding
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['id'], row['title'], row['overview'], row['synthetic_vibe'],
                row['poster_url'], row['trailer_url'], row['director'], 
                row['cast'], row['writer'], row['composer'],
                int(float(row['runtime'])) if row['runtime'] else 0,
                float(row['vote_average']) if row['vote_average'] else 0.0,
                float(row['popularity']) if row['popularity'] else 0.0, # Mapped Popularity
                int(float(row['year'])) if row['year'] else 0,
                row['genres'], row['tagline'], vector
            ))
        except Exception as e:
            print(f"Skipping {row.get('title', 'Unknown')}: {e}")
        
        # Adjust sleep based on your Tier (Free tier: ~15 RPM, Paid: 2000+ RPM)
        time.sleep(0.02) 

    # 4. OPTIMIZED INDEXING
    print("⚡ Building Hybrid Indexes...")
    # Keyword Index (GIN)
    cur.execute("CREATE INDEX idx_search_vector ON movies USING GIN (search_vector);")
    # Semantic Index (HNSW)
    cur.execute("CREATE INDEX idx_embedding ON movies USING hnsw (embedding vector_cosine_ops);")
    
    conn.commit()
    cur.close()
    conn.close()
    print("🚀 Ingestion Complete! Database is updated and indexed.")

if __name__ == "__main__":
    ingest_production()