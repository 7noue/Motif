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
def vector_search(q: str, limit: int = 20, offset: int = 0):
    """
    Args:
        q: The search query
        limit: How many to return to UI (Default 20)
        offset: For pagination (e.g., 0 for page 1, 20 for page 2)
    """
    vector = get_query_embedding(q)
    if not vector:
        raise HTTPException(status_code=500, detail="Failed to generate embedding")

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    
    try:
        cur = conn.cursor()
        
        # 1. FETCH CANDIDATES (The "Broad Net")
        # For 5,000 films, we grab the top 100 vectors.
        # This ensures our "Re-Ranking" has enough data to work with.
        sql = """
            SELECT id, title, synthetic_vibe, poster_url, overview,
                   director, cast_members, runtime, rating, release_year, genres, tagline,
                   (embedding <=> %s::vector) as distance
            FROM movies
            ORDER BY distance ASC
            LIMIT 100 
        """
        
        cur.execute(sql, (vector,))
        rows = cur.fetchall()
        
        # 2. PROCESS & FILTER
        candidates = []
        for r in rows:
            raw_sim = 1 - r[12]
            
            # Use your curve logic here...
            min_threshold = 0.25
            max_expected = 0.60 

            if raw_sim < min_threshold:
                 final_score = 0.0
            else:
                 normalized = (raw_sim - min_threshold) / (max_expected - min_threshold)
                 final_score = max(0.0, min(0.99, normalized))

            if final_score > 0.40:
                candidates.append({
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
                    "match_score": final_score,
                    "display_score": f"{final_score:.0%}" 
                })

        # 3. RE-RANKING
        query_lower = q.lower()
        if any(w in query_lower for w in ["best", "top", "rated", "highest", "masterpiece"]):
            candidates.sort(key=lambda x: x["rating"], reverse=True)
        else:
            candidates.sort(key=lambda x: x["match_score"], reverse=True)

        # 4. PAGINATION (The "Return Narrow" Step)
        # Slices the list based on what the frontend asked for.
        # e.g., list[0:20] for page 1, list[20:40] for page 2
        start = offset
        end = offset + limit
        
        return candidates[start:end]

    except Exception as e:
        print(f"SQL Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/explain")
def explain_recommendation(payload: dict):
    """
    Uses GEMINI to explain the match (Reasoning Agent).
    v2.0: Optimized to leverage the "Meme-First" database tags.
    """
    movie = payload.get("movie")
    query = payload.get("query")
    vibe = payload.get("vibe") # This now contains "Sigma", "Coquette", etc.
    score = payload.get("human_score", "high")

    # 🔥 NEW PROMPT: The "Context Decoder"
    prompt = f"""
    You are Motif, the AI engine that explains film through internet culture.
    
    DATA CONTEXT:
    - User Query: "{query}"
    - Movie: "{movie}"
    - THE VIBE (Ground Truth): "{vibe}"
    
    TASK:
    The 'Vibe' field contains specific internet archetypes (e.g., Sigma, Coquette, Doomer).
    Your job is to bridge the User's Query to that Vibe.

    GUIDELINES:
    1. **Trust the Vibe:** If the Vibe says "Sigma Male manifesto," and the user asked for "Sigma," EXPLICITLY reference that connection. Don't be vague.
    2. **Explain the "Why":** Why is this movie considered "Coquette"? (e.g., "Because of the pastel color palette and Lana Del Rey energy").
    3. **Tone:** Knowledgeable, slightly online, but helpful.
    4. **Length:** 2-3 punchy sentences (max 60 words).

    EXAMPLES:
    - Query: "literally me" -> Vibe: "Lonely Doomer sci-fi..." 
      -> Response: "This is the ultimate 'Literally Me' film. The 'Doomer' aesthetic of a lonely holographic romance perfectly captures the modern feeling of isolation."

    - Query: "girlboss" -> Vibe: "Unihinged female rage..."
      -> Response: "It defines the 'Good for Her' genre. The main character's descent into unhinged madness became a viral symbol of toxic female empowerment."

    YOUR EXPLANATION:
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
        )
        return {"reason": response.text}
    except Exception as e:
        return {"reason": f"It matches the vibe: {vibe}. (System error: {str(e)})"}