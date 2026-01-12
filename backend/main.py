from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# DB Config
DB_PARAMS = {
    "host": "localhost",
    "database": "motif_db",
    "user": "postgres",
    "password": "password"
}

client = genai.Client(api_key=GEMINI_API_KEY)
app = FastAPI(title="Motif Semantic Engine v2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = psycopg2.connect(**DB_PARAMS, cursor_factory=RealDictCursor)
    return conn

def get_embedding(text: str):
    try:
        response = client.models.embed_content(
            model="text-embedding-004",
            contents=text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"Embedding error: {e}")
        return None

@app.get("/search")
def hybrid_search(q: str, limit: int = 20, offset: int = 0):
    vector = get_embedding(q)
    conn = get_db()
    try:
        cur = conn.cursor()
        
        # WEIGTHING: 60% Vibe, 30% Keyword, 10% Popularity
        query = """
            WITH semantic_results AS (
                SELECT id, 1 - (embedding <=> %s::vector) as sim_score
                FROM movies
                ORDER BY embedding <=> %s::vector
                LIMIT 100
            ),
            keyword_results AS (
                SELECT id, ts_rank_cd(search_vector, websearch_to_tsquery('english', %s)) as lex_score
                FROM movies
                WHERE search_vector @@ websearch_to_tsquery('english', %s)
                LIMIT 100
            )
            SELECT 
                m.id, m.title, m.synthetic_vibe, m.poster_url, m.director, 
                m.cast_members, m.release_year, m.rating, m.popularity,
                COALESCE(s.sim_score, 0) as semantic_score,
                COALESCE(k.lex_score, 0) as keyword_score
            FROM movies m
            LEFT JOIN semantic_results s ON m.id = s.id
            LEFT JOIN keyword_results k ON m.id = k.id
            WHERE s.id IS NOT NULL OR k.id IS NOT NULL
            ORDER BY (
                (COALESCE(s.sim_score, 0) * 0.6) + 
                (COALESCE(k.lex_score, 0) * 0.3) + 
                (LOG(GREATEST(m.popularity, 1)) / 10.0 * 0.1)
            ) DESC
            OFFSET %s LIMIT %s;
        """
        
        cur.execute(query, (vector, vector, q, q, offset, limit))
        rows = cur.fetchall()
        
        # --- THE CRITICAL UI MAPPING STEP ---
        formatted_results = []
        for r in rows:
            # Calculate a combined score for the UI progress bar
            raw_score = (r['semantic_score'] * 0.6) + (min(r['keyword_score'], 1) * 0.3)
            # Add a small bump for popularity to the display score
            display_score = min(raw_score + 0.1, 0.99) 

            formatted_results.append({
                "id": r['id'],
                "title": r['title'],
                "vibe": r['synthetic_vibe'],
                "poster_url": r['poster_url'],
                "director": r['director'],
                "cast": r['cast_members'],
                "year": r['release_year'],
                "rating": float(r['rating']),
                "match_score": f"{display_score:.0%}" # e.g. "85%"
            })

        return formatted_results
    finally:
        conn.close()

@app.post("/explain")
def explain_recommendation(payload: dict):
    movie = payload.get("movie")
    query = payload.get("query")
    vibe = payload.get("vibe")
    director = payload.get("director")

    prompt = f"""
    You are MOTIF, a high-taste cinematic curator. You don't use "AI speak." 
    You understand that movies are about 'feeling' and 'cultural moments.'

    CONTEXT:
    The user is looking for: "{query}"
    You found them: "{movie}" (Directed by {director})
    The film's Vibe Lore is: "{vibe}"

    TASK:
    Write a 2-3 sentence recommendation. 
    - Sentence 1: Validate their search by connecting it to the film's "aesthetic dna."
    - Sentence 2: Mention the director's style or a specific "mood" (e.g., "it's perfect for a rainy Tuesday").
    - Tone: Like a text from a friend who watches too many movies. Use words like 'lore', 'canon', 'unhinged', or 'peak' ONLY if they fit naturally.

    RULES:
    - NO: "This movie is a great choice because..."
    - NO: "Based on your query..."
    - START WITH: A natural opener like "Honestly," "If you're chasing that..." or "This is basically the blueprint for..."

    PITCH:
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt
        )
        # Clean up formatting for the UI
        reason = response.text.strip().replace('"', '')
        return {"reason": reason}
    except Exception:
        return {"reason": "Honestly, this just hits the exact frequency you're looking for. It's a total mood reset."}