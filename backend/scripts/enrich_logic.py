import os
import json
import time
import sqlite3
import requests
from dotenv import load_dotenv
import ollama
from openai import OpenAI

load_dotenv()

# --- CONFIG ---
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
OR_CLIENT = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)
OR_MODEL = "google/gemini-2.0-flash-exp:free"

DELAY_BETWEEN_CALLS = 0.35  # seconds
MAX_SIMILAR_FILMS = 5
DB_PATH = "enriched_movies.db"

# --- SETUP SQLITE DB ---
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS movies (
    tmdb_id INTEGER PRIMARY KEY,
    title TEXT,
    year INTEGER,
    overview TEXT,
    runtime INTEGER,
    director TEXT,
    cast TEXT,
    original_language TEXT,
    poster_url TEXT,
    trailer_url TEXT,
    certification TEXT,
    streaming_info TEXT,
    primary_aesthetic TEXT,
    fit_quote TEXT,
    social_friction TEXT,
    focus_load TEXT,
    tone_label TEXT,
    emotional_aftertaste TEXT,
    perfect_occasion TEXT,
    similar_films TEXT,
    vibe_signature_label TEXT,
    vibe_signature_val INTEGER,
    palette_name TEXT,
    palette_colors TEXT,
    checkpointed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# --- TMDB HELPERS ---
def fetch_tmdb_details(tmdb_id):
    base_url = "https://api.themoviedb.org/3"

    details = requests.get(f"{base_url}/movie/{tmdb_id}", params={"api_key": TMDB_API_KEY, "language": "en-US"}).json()
    time.sleep(DELAY_BETWEEN_CALLS)

    credits = requests.get(f"{base_url}/movie/{tmdb_id}/credits", params={"api_key": TMDB_API_KEY}).json()
    time.sleep(DELAY_BETWEEN_CALLS)

    release_resp = requests.get(f"{base_url}/movie/{tmdb_id}/release_dates", params={"api_key": TMDB_API_KEY}).json()
    cert_code = "NR"
    for entry in release_resp.get("results", []):
        if entry["iso_3166_1"] == "US" and entry.get("release_dates"):
            cert_code = entry["release_dates"][0].get("certification", "NR")
            break
    time.sleep(DELAY_BETWEEN_CALLS)

    stream_resp = requests.get(f"{base_url}/movie/{tmdb_id}/watch/providers", params={"api_key": TMDB_API_KEY}).json()
    streaming_data = stream_resp.get("results", {}).get("US", {})
    streaming_info = []
    for key in ["flatrate", "rent", "buy"]:
        if key in streaming_data:
            streaming_info.extend([p["provider_name"] for p in streaming_data[key]])
    time.sleep(DELAY_BETWEEN_CALLS)

    similar_resp = requests.get(f"{base_url}/movie/{tmdb_id}/similar", params={"api_key": TMDB_API_KEY, "language": "en-US"}).json()
    similar_movies = [m["title"] for m in similar_resp.get("results", [])[:MAX_SIMILAR_FILMS]]
    time.sleep(DELAY_BETWEEN_CALLS)

    return {
        "tmdb_id": tmdb_id,
        "title": details.get("title"),
        "year": int(details.get("release_date", "0000")[:4]),
        "overview": details.get("overview"),
        "runtime": details.get("runtime"),
        "director": next((c["name"] for c in credits.get("crew", []) if c["job"] == "Director"), "Unknown"),
        "cast": [c["name"] for c in credits.get("cast", [])[:5]],
        "original_language": details.get("original_language"),
        "poster_url": f"https://image.tmdb.org/t/p/w500{details.get('poster_path')}" if details.get("poster_path") else None,
        "trailer_url": get_trailer_url(tmdb_id),
        "certification": cert_code,
        "streaming_info": ", ".join(streaming_info) if streaming_info else None,
        "similar_films": similar_movies
    }

def get_trailer_url(tmdb_id):
    videos = requests.get(f"https://api.themoviedb.org/3/movie/{tmdb_id}/videos", params={"api_key": TMDB_API_KEY}).json().get("results", [])
    for vid in videos:
        if vid["site"] == "YouTube" and vid["type"] == "Trailer":
            return f"https://www.youtube.com/watch?v={vid['key']}"
    return None

# --- AI ENRICHMENT ---
def _get_prompt(movie):
    return f"""
### SYSTEM ROLE: CULTURAL CURATOR
Analyze film: "{movie['title']}" ({movie.get('year', '')}).
Synopsis: {movie['overview']}

### TASK: Generate strict JSON metadata.
1. AESTHETIC LABEL (Max 2 words)
2. THE FIT (Max 15 words)
3. SOCIAL FRICTION
4. FOCUS LOAD
5. TONE
6. EMOTIONAL AFTERTASTE
7. PERFECT OCCASION
8. SIMILAR FILMS (max 5)
9. VIBE SIGNATURE COLORS (top 3 hex)
### OUTPUT JSON:
{{
    "primary_aesthetic": "string",
    "fit_quote": "string",
    "social_friction": "string",
    "focus_load": "string",
    "tone_label": "string",
    "emotional_aftertaste": "string",
    "perfect_occasion": "string",
    "similar_films": ["A","B","C","D","E"],
    "vibe_signature": {{"label":"string","val_percent":0}},
    "palette": {{"name":"string","colors":["#000000","#FFFFFF","#123456"]}}
}}
"""

def generate_via_ollama(movie):
    try:
        response = ollama.chat(
            model="llama3.1",
            messages=[{"role": "user", "content": _get_prompt(movie)}],
            format="json"
        )
        return json.loads(response['message']['content'])
    except Exception as e:
        print(f"⚠️ Ollama fail: {e}")
        return None

def generate_via_openrouter(movie):
    try:
        response = OR_CLIENT.chat.completions.create(
            model=OR_MODEL,
            messages=[
                {"role": "system", "content": "Return only valid JSON."},
                {"role": "user", "content": _get_prompt(movie)}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"⚠️ OpenRouter fail: {e}")
        return None

# --- SAVE TO SQLITE ---
def save_to_db(movie):
    cursor.execute("""
    INSERT OR REPLACE INTO movies (
        tmdb_id,title,year,overview,runtime,director,cast,original_language,poster_url,trailer_url,
        certification,streaming_info,primary_aesthetic,fit_quote,social_friction,focus_load,tone_label,
        emotional_aftertaste,perfect_occasion,similar_films,vibe_signature_label,vibe_signature_val,
        palette_name,palette_colors
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        movie["tmdb_id"],
        movie["title"],
        movie["year"],
        movie["overview"],
        movie["runtime"],
        movie["director"],
        ", ".join(movie["cast"]),
        movie["original_language"],
        movie["poster_url"],
        movie["trailer_url"],
        movie["certification"],
        movie["streaming_info"],
        movie.get("primary_aesthetic"),
        movie.get("fit_quote"),
        movie.get("social_friction"),
        movie.get("focus_load"),
        movie.get("tone_label"),
        movie.get("emotional_aftertaste"),
        movie.get("perfect_occasion"),
        ", ".join(movie.get("similar_films", [])),
        movie.get("vibe_signature", {}).get("label"),
        movie.get("vibe_signature", {}).get("val_percent"),
        movie.get("palette_name"),
        ", ".join(movie.get("palette_colors", []))
    ))
    conn.commit()

# --- ENRICH AND SAVE ---
def enrich_and_save(tmdb_id):
    movie_data = fetch_tmdb_details(tmdb_id)
    metadata = generate_via_ollama(movie_data) or generate_via_openrouter(movie_data) or {}
    
    # Correct vibe %
    vibe_val = metadata.get("vibe_signature", {}).get("val_percent", 0)
    metadata["vibe_signature"]["val_percent"] = min(max(vibe_val, 0), 100)

    enriched_movie = {
        **movie_data,
        "primary_aesthetic": metadata.get("primary_aesthetic"),
        "fit_quote": metadata.get("fit_quote"),
        "social_friction": metadata.get("social_friction"),
        "focus_load": metadata.get("focus_load"),
        "tone_label": metadata.get("tone_label"),
        "emotional_aftertaste": metadata.get("emotional_aftertaste"),
        "perfect_occasion": metadata.get("perfect_occasion"),
        "similar_films": metadata.get("similar_films", movie_data.get("similar_films", [])),
        "vibe_signature": metadata.get("vibe_signature"),
        "palette_name": metadata.get("palette", {}).get("name"),
        "palette_colors": metadata.get("palette", {}).get("colors")
    }

    save_to_db(enriched_movie)
    return enriched_movie

# --- EXAMPLE USAGE ---
if __name__ == "__main__":
    tmdb_ids = [603, 550, 680]  # Example TMDB IDs
    for tid in tmdb_ids:
        movie = enrich_and_save(tid)
        print(f"✅ Saved {movie['title']} to DB with checkpoint")
