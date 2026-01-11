import pandas as pd
from google import genai
from google.genai import types  # <--- NEW: Needed for config
import psycopg2
from pgvector.psycopg2 import register_vector
import time
from tqdm import tqdm
from dotenv import load_dotenv
import os 

# --- CONFIGURATION ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DB_HOST = "localhost"
DB_NAME = "motif_db"
DB_USER = "postgres"
DB_PASS = "password"

# FIX 1: Use the variable, not a string
client = genai.Client(api_key=GEMINI_API_KEY)

# --- 1. PREPARE DATABASE ---
print("🔌 Connecting to DB...")
conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
cur = conn.cursor()
cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

print("🛠️ Creating Schema (With Keywords & Tagline)...")
cur.execute("DROP TABLE IF EXISTS movies")
cur.execute("""
    CREATE TABLE movies (
        id SERIAL PRIMARY KEY,
        tmdb_id INTEGER,
        title TEXT,
        overview TEXT,
        synthetic_vibe TEXT,
        poster_url TEXT,
        trailer_url TEXT,
        genres TEXT,
        keywords TEXT,    
        tagline TEXT,     
        embedding vector(768) 
    )
""")
conn.commit()

# --- 2. LOAD & PREPARE DATA ---
print("📂 Loading Enriched CSV...")
# Ensure this CSV exists in your folder
# df = pd.read_csv("motif_mvp_5000_enriched.csv")
df = pd.read_csv("motif_mvp_100_local.csv")
df.fillna("", inplace=True)

def create_rag_content(row):
    vibe = f"Mood & Aesthetic: {row['synthetic_vibe']}"
    identity = f"Title: {row['title']}. Theme: {row['tagline']}"
    kw_raw = str(row.get('keywords_str', ''))
    keywords = f"Keywords: {kw_raw[:200]}" 
    return f"{vibe}. {identity}. {keywords}."

print("🔗 Generating RAG strings...")
df['rag_content'] = df.apply(create_rag_content, axis=1)

# --- 3. EMBED & INSERT ---
print("🧠 Generating Embeddings (Gemini)...")

def get_embedding(text):
    try:
        # FIX 2: Use client.models.embed_content
        response = client.models.embed_content(
            model="text-embedding-004",
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT" # Optimizes vector for storage/lookup
            )
        )
        # FIX 3: Access object attributes, not dictionary keys
        return response.embeddings[0].values
    except Exception as e:
        print(f"Error embedding text: {e}")
        return None

count = 0
for index, row in tqdm(df.iterrows(), total=df.shape[0]):
    vector = get_embedding(row['rag_content'])
    
    if vector:
        cur.execute("""
            INSERT INTO movies (tmdb_id, title, overview, synthetic_vibe, poster_url, trailer_url, genres, keywords, tagline, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            row['id'],
            row['title'],
            row['overview'],
            row['synthetic_vibe'],
            row['poster_url'],
            row['trailer_url'],
            row['genres_str'],
            row['keywords_str'],
            row['tagline'],
            vector
        ))
        count += 1
        time.sleep(0.05) # Reduced sleep slightly for speed

conn.commit()

# --- 4. INDEX ---
print("⚡ Creating HNSW Index...")
cur.execute("CREATE INDEX ON movies USING hnsw (embedding vector_cosine_ops);")
conn.commit()
cur.close()
conn.close()

print(f"✅ SUCCESS! Ingested {count} movies.")