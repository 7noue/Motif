import os
import json
import time
import sqlite3
import requests
from dotenv import load_dotenv
import ollama
import logging
import pandas as pd
from tqdm import tqdm  # This tracks the process

load_dotenv()

# --- CONFIG ---
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

DELAY_BETWEEN_CALLS = 0.35  # seconds
MAX_SIMILAR_FILMS = 5
DB_PATH = "enriched_movies.db"

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("EnrichmentEngine")

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

# --- TMDB HELPERS (OPTIMIZED) ---
def fetch_tmdb_details(tmdb_id):
    base_url = "https://api.themoviedb.org/3"
    
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
        "append_to_response": "credits,release_dates,watch/providers,similar,videos"
    }
    
    try:
        response = requests.get(f"{base_url}/movie/{tmdb_id}", params=params)
        
        if response.status_code != 200:
            logger.warning(f"Skipping ID {tmdb_id}: TMDB returned {response.status_code}")
            return {}
            
        data = response.json()
        
        director = "Unknown"
        cast = []
        if "credits" in data:
            director = next((c["name"] for c in data["credits"].get("crew", []) if c["job"] == "Director"), "Unknown")
            cast = [c["name"] for c in data["credits"].get("cast", [])[:5]]

        cert_code = "NR"
        if "release_dates" in data:
            for entry in data["release_dates"].get("results", []):
                if entry["iso_3166_1"] == "US":
                    for date in entry.get("release_dates", []):
                        if date.get("certification"):
                            cert_code = date["certification"]
                            break
                    if cert_code != "NR": break

        streaming_info = []
        if "watch/providers" in data:
            providers = data["watch/providers"].get("results", {}).get("US", {})
            for key in ["flatrate", "rent", "buy"]:
                if key in providers:
                    streaming_info.extend([p["provider_name"] for p in providers[key]])
        streaming_info = list(set(streaming_info))

        similar_movies = []
        if "similar" in data:
            similar_movies = [m["title"] for m in data["similar"].get("results", [])[:MAX_SIMILAR_FILMS]]

        trailer_url = None
        if "videos" in data:
            for vid in data["videos"].get("results", []):
                if vid["site"] == "YouTube" and vid["type"] == "Trailer":
                    trailer_url = f"https://www.youtube.com/watch?v={vid['key']}"
                    break

        time.sleep(DELAY_BETWEEN_CALLS) 

        return {
            "tmdb_id": tmdb_id,
            "title": data.get("title"),
            "year": int(data.get("release_date", "0000")[:4]) if data.get("release_date") else 0,
            "overview": data.get("overview"),
            "runtime": data.get("runtime"),
            "director": director,
            "cast": cast,
            "original_language": data.get("original_language"),
            "poster_url": f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}" if data.get("poster_path") else None,
            "trailer_url": trailer_url,
            "certification": cert_code,
            "streaming_info": ", ".join(streaming_info) if streaming_info else None,
            "similar_films": similar_movies
        }
    except Exception as e:
        logger.error(f"Error fetching ID {tmdb_id}: {e}")
        return {}

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
        logger.error(f"⚠️ Ollama fail: {e}")
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
    try:
        movie_data = fetch_tmdb_details(tmdb_id)
        if not movie_data.get("title"):
            return None

        metadata = generate_via_ollama(movie_data)
        
        if not metadata:
            logger.error(f"ID {tmdb_id}: AI generation failed.")
            return None

        vibe_val = metadata.get("vibe_signature", {}).get("val_percent", 0)
        if metadata.get("vibe_signature"):
            metadata["vibe_signature"]["val_percent"] = min(max(vibe_val, 0), 100)
        else:
            metadata["vibe_signature"] = {"label": "Unknown", "val_percent": 0}

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
            "palette": metadata.get("palette", {}),
            "palette_name": metadata.get("palette", {}).get("name"),
            "palette_colors": metadata.get("palette", {}).get("colors")
        }

        save_to_db(enriched_movie)
        return enriched_movie
    except Exception as e:
        logger.error(f"Critical error on ID {tmdb_id}: {e}")
        return None

# --- MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    input_file = "backend/data/cleaned_movies.csv"
    
    if not os.path.exists(input_file):
        logger.error(f"File not found: {input_file}")
        exit()

    logger.info("Loading dataset...")
    df = pd.read_csv(input_file)
    
    df = df.sort_values(by='popularity', ascending=False).head(5000).copy()
    
    existing_ids_query = cursor.execute("SELECT tmdb_id FROM movies").fetchall()
    existing_ids = set(row[0] for row in existing_ids_query)
    
    id_col = 'id' if 'id' in df.columns else 'tmdb_id'
    all_ids = df[id_col].tolist()
    ids_to_process = [tid for tid in all_ids if tid not in existing_ids]

    logger.info(f"Total: {len(all_ids)} | Done: {len(existing_ids)} | Queue: {len(ids_to_process)}")

    for tid in tqdm(ids_to_process, desc="Enriching Movies", unit="film"):
        enrich_and_save(tid)
            
    logger.info("Batch processing complete.")
    conn.close()