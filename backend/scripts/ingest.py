import pandas as pd
from google import genai
from google.genai import types
import psycopg2
import time
from tqdm import tqdm
from dotenv import load_dotenv
import os 

# --- CONFIGURATION ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ⚠️ UPDATE WITH YOUR DB CREDENTIALS
DB_HOST = "localhost"
DB_NAME = "motif_db"
DB_USER = "postgres"
DB_PASS = "password" 

if not GEMINI_API_KEY:
    raise ValueError("❌ Missing GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

# --- 1. PREPARE DATABASE ---
print("🔌 Connecting to DB...")
try:
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
except Exception as e:
    raise ConnectionError(f"❌ Could not connect to Postgres. Error: {e}")

cur = conn.cursor()
cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

print("🛠️ Creating Schema (Expanded for Metadata)...")
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
        director TEXT,
        cast_members TEXT,
        writer TEXT,
        composer TEXT,
        runtime INTEGER,
        rating NUMERIC(3,1),
        release_year INTEGER,
        genres TEXT,
        keywords TEXT,    
        tagline TEXT,     
        embedding vector(768) 
    )
""")
conn.commit()

# --- 2. LOAD & PREPARE DATA ---
# 🛡️ ROBUST PATH FINDING
# This ensures we find the file relative to THIS script, no matter where you run it from.
script_dir = os.path.dirname(os.path.abspath(__file__))
input_csv = os.path.join(script_dir, "../data/motif_final_rag.csv")

if not os.path.exists(input_csv):
    raise FileNotFoundError(f"❌ Could not find {input_csv}. \n   Did you run '2_construct_rag.py' to generate the final CSV?")

print(f"📂 Loading Data from {input_csv}...")
df = pd.read_csv(input_csv)
df.fillna("", inplace=True)

if 'rag_content' not in df.columns:
    raise ValueError("❌ CSV is missing 'rag_content' column! Run Script 2 first.")

# --- 3. EMBED & INSERT ---
print("🧠 Generating Embeddings (Gemini text-embedding-004)...")

def get_embedding(text):
    try:
        response = client.models.embed_content(
            model="text-embedding-004",
            contents=text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"⚠️ Embedding Error: {e}")
        return None

count = 0
for index, row in tqdm(df.iterrows(), total=df.shape[0]):
    text_to_embed = row['rag_content']
    vector = get_embedding(text_to_embed)
    
    if vector:
        cur.execute("""
            INSERT INTO movies (
                tmdb_id, title, overview, synthetic_vibe, 
                poster_url, trailer_url, 
                director, cast_members, writer, composer,
                runtime, rating, release_year,
                genres, keywords, tagline, embedding
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            row['id'], row['title'], row['overview'], row['synthetic_vibe'],
            row['poster_url'], row['trailer_url'],
            row.get('director', ''), 
            row.get('cast', ''),           # Maps CSV 'cast' -> DB 'cast_members'
            row.get('writer', ''), 
            row.get('composer', ''),
            int(row.get('runtime', 0)) if row.get('runtime') != '' else 0,
            float(row.get('vote_average', 0)) if row.get('vote_average') != '' else 0.0,
            int(row.get('year', 0)) if row.get('year') != '' else 0,
            row.get('genres_str', ''), 
            row.get('keywords_str', ''), 
            row.get('tagline', ''),
            vector
        ))
        count += 1
        time.sleep(0.1) # Rate limit safety

conn.commit()

# --- 4. INDEX ---
print("⚡ Creating HNSW Index (The Gold Standard)...")
# HNSW is significantly faster for vector search than IVFFlat.
cur.execute("CREATE INDEX ON movies USING hnsw (embedding vector_cosine_ops);")
conn.commit()
cur.close()
conn.close()

print(f"✅ SUCCESS! Ingested {count} movies into Postgres.")