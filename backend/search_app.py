from google import genai
from google.genai import types
import psycopg2
import json
from dotenv import load_dotenv
import os
import time 

# --- CONFIGURATION ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DB_HOST = "localhost"
DB_NAME = "motif_db"
DB_USER = "postgres"
DB_PASS = "password" 

# 1. Initialize Client (The NEW way)
client = genai.Client(api_key=GEMINI_API_KEY)

# --- PART A: VECTOR SEARCH (RETRIEVAL) ---
def get_query_embedding(text):
    try:
        # FIX: Use client.models.embed_content
        result = client.models.embed_content(
            model="text-embedding-004",
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY" # Crucial: optimized for search queries
            )
        )
        # FIX: Return object attribute, not dict key
        return result.embeddings[0].values
    except Exception as e:
        print(f"Embedding Error: {e}")
        return None

def search_movies(user_query, top_k=5):
    """
    Fast Retrieval. Filters out garbage matches (Distance > 0.48).
    """
    vector = get_query_embedding(user_query)
    if not vector: return []

    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    
    # Select everything we need for the UI and the 'Reasoning' step
    # Note: <=> is Cosine Distance operator in pgvector
    sql = """
        SELECT title, synthetic_vibe, keywords, tagline, overview, poster_url, 
               (embedding <=> %s::vector) as distance
        FROM movies
        ORDER BY distance ASC
        LIMIT %s
    """
    cur.execute(sql, (vector, top_k))
    results = cur.fetchall()
    conn.close()
    
    movies = []
    for r in results:
        dist = r[6]
        # GUARDRAIL: Distance Threshold
        # 0.0 = Exact match. > 0.48 is usually loose/irrelevant.
        if dist > 0.48: 
            continue 
            
        movies.append({
            "title": r[0],
            "vibe": r[1],
            "keywords": r[2],
            "tagline": r[3],
            "overview": r[4],
            "poster": r[5],
            "score": f"{(1-dist):.2%}"
        })
    
    return movies

# --- PART B: THE JUDGE (ON-CLICK REASONING) ---
def get_verified_reasoning(user_query, movie):
    """
    The 'Movie Buff' Agent. 
    Explains the recommendation like a friend, not a robot.
    """
    
    context = (
        f"Movie: {movie['title']}\n"
        f"Vibe: {movie['vibe']}\n"
        f"Keywords: {movie['keywords']}\n" 
        f"Overview: {movie['overview'][:200]}..." 
    )

    # 2. The "Movie Buff" Prompt
    prompt = f"""
    Act as a savvy movie recommender talking to a friend.
    
    The Friend asked for: "{user_query}"
    You found this movie:
    {context}
    
    Task:
    1. Score the match (0-100).
    2. If Score > 70, write a short, punchy reason why they should watch it.
    
    CRITICAL RULES for the Reason:
    - DO NOT say "The user asked for..." or "This movie matches your query because..."
    - DO NOT be robotic.
    - BE DIRECT. e.g., "If you want anxiety, this is the ultimate stress test." or "It literally features the scene you described."
    - Mention specific details from the 'Vibe' (like memes or actors).
    
    Output JSON:
    {{ "score": 85, "reason": "Reasoning text..." }}
    """
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash", 
                contents=prompt, 
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            data = json.loads(response.text)
            score = data.get("score", 0)
            
            if score < 70:
                return None 
                
            return data.get("reason")
            
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                time.sleep((attempt + 1) * 2)
            else:
                return None
    return None

# --- SIMULATION ---
if __name__ == "__main__":
    # Test 1: A Real "Motif" Query
    query = "Inception"
    print(f"\n🔎 Searching for: '{query}'")
    
    matches = search_movies(query)
    
    if not matches:
        print("❌ No good matches found (Threshold blocked).")
    else:
        for i, m in enumerate(matches):
            print(f"\n[{i+1}] {m['title']} (Match: {m['score']})")
            print(f"    Vibe: {m['vibe']}")
            
            # SIMULATE USER CLICKING THE FIRST RESULT
            if i == 0:
                print("    👉 User clicked! Verifying reasoning...")
                reason = get_verified_reasoning(query, m)
                if reason:
                    print(f"    ✅ AI Reasoning: {reason}")
                else:
                    print(f"    ⚠️ AI withheld reasoning (Confidence too low).")