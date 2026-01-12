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
    Now upgraded to understand MEMES, CULT STATUS, and CONTEXT.
    """
    movie = payload.get("movie")
    query = payload.get("query")
    vibe = payload.get("vibe")
    score = payload.get("human_score", "high") # Use this to gauge enthusiasm if needed

    # 🔥 NEW PROMPT: The "Chronically Online" Film Expert
    prompt = f"""
    You are Motif, an AI engine deeply plugged into film culture, internet lore, and memes.
    
    CONTEXT:
    - User Query: "{query}"
    - Selected Movie: "{movie}"
    - Database Vibe: "{vibe}"
    
    TASK:
    Explain the connection between the Query and the Movie. 
    Don't just describe the plot—explain the *culture* or the *meme* behind it.

    GUIDELINES:
    1. **Identify the Meme:** If the query references a specific meme (e.g., "sigma", "loca", "literally me"), explain its origin or why it's trending.
    2. **The "Sauce":** If it's just a vibe query, explain exactly *how* the movie nails that aesthetic (cinematography, soundtrack, iconic scenes).
    3. **Tone:** Insightful, modern, and culturally aware. Like a video essayist condensing their thoughts into a paragraph.
    4. **Length:** 2-3 punchy sentences (approx 40-60 words).

    EXAMPLES:
    - Query: "where have you been loca" -> Movie: "Twilight: New Moon" 
      -> Response: "This references the unintentionally hilarious line Jacob Black delivers to Bella. It blew up on TikTok as the ultimate example of the saga's campy, melodramatic dialogue that fans obsess over."
    
    - Query: "sigma male grindset" -> Movie: "American Psycho" 
      -> Response: "Patrick Bateman is the face of the ironic 'Sigma' meme culture. The internet repurposed his corporate emptiness into a satire on hustle culture and toxic masculinity."

    - Query: "neon lonely driver" -> Movie: "Drive" 
      -> Response: "The film that launched a thousand 'literally me' memes. It defines the synthwave aesthetic, combining Ryan Gosling's stoic performance with a neon-drenched LA nightscape."

    YOUR EXPLANATION:
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
        )
        return {"reason": response.text}
    except Exception as e:
        return {"reason": f"This is a match based on the vibe: {vibe}. (System error: {str(e)})"}