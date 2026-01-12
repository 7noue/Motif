from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
import psycopg2
import os
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Database Credentials
DB_HOST = "localhost"
DB_NAME = "motif_db"
DB_USER = "postgres"
DB_PASS = "password" # UPDATE THIS TO YOUR REAL PASSWORD

# Initialize Gemini Client
client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI(title="Motif API (Gemini + Postgres)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- HELPER: Database Connection ---
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS
        )
        return conn
    except Exception as e:
        print(f"❌ DB Connection Error: {e}")
        return None

# --- HELPER: Embed Query (GEMINI) ---
def get_query_embedding(text):
    """
    Generates a vector using Gemini.
    CRITICAL: Uses 'RETRIEVAL_QUERY' to match your ingestion 'RETRIEVAL_DOCUMENT'.
    """
    try:
        response = client.models.embed_content(
            model="text-embedding-004",
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY" 
            )
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"⚠️ Embedding Error: {e}")
        return None

# --- ROUTES ---

@app.get("/")
def health_check():
    conn = get_db_connection()
    status = "connected" if conn else "failed"
    if conn: conn.close()
    return {"status": "online", "database": status}

@app.get("/search")
def vector_search(q: str):
    """
    1. Embeds query with Gemini.
    2. Searches Postgres for nearest neighbors.
    3. Returns RICH metadata (Director, Cast, Runtime, etc.)
    """
    vector = get_query_embedding(q)
    if not vector:
        raise HTTPException(status_code=500, detail="Failed to generate embedding")

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    
    try:
        cur = conn.cursor()
        
        # UPDATED SQL: Fetching all the new columns we ingested
        sql = """
            SELECT id, title, synthetic_vibe, poster_url, overview,
                   director, cast_members, runtime, rating, release_year, genres, tagline,
                   (embedding <=> %s::vector) as distance
            FROM movies
            ORDER BY distance ASC
            LIMIT 10
        """
        
        cur.execute(sql, (vector,))
        rows = cur.fetchall()
        
        results = []
        for r in rows:
            # Distance < 0.65 is our similarity threshold
            # r[12] is the distance column now (13th item, index 12)
            if r[12] < 0.65:
                results.append({
                    "id": r[0],
                    "title": r[1],
                    "vibe": r[2],
                    "poster_url": r[3],
                    "overview": r[4],
                    "director": r[5],
                    "cast": r[6],
                    "runtime": r[7],
                    "rating": float(r[8]) if r[8] else 0.0,
                    "year": r[9],
                    "genres": r[10],
                    "tagline": r[11],
                    "match_score": f"{(1 - r[12]):.2%}"
                })
        
        return results

    except Exception as e:
        print(f"SQL Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/explain")
def explain_recommendation(payload: dict):
    """
    Uses GEMINI to explain the match (Reasoning Agent).
    """
    movie = payload.get("movie")
    query = payload.get("query")
    vibe = payload.get("vibe")

    prompt = f"""
    You are a blunt movie friend.
    User wanted: "{query}"
    You suggested: "{movie}"
    The Vibe is: "{vibe}"

    Write 1 short sentence (max 20 words) explaining why this fits.
    Be specific. Mention the 'Sauce' or aesthetic.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
        )
        return {"reason": response.text}
    except Exception as e:
        return {"reason": f"It fits the vibe. (Gemini error: {str(e)})"}