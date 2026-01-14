import os
import json
import time
import sqlite3
import requests
from dotenv import load_dotenv
import ollama
from openai import OpenAI
import logging
import pandas as pd
from tqdm import tqdm  # This tracks the process

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

# --- TMDB HELPERS ---
def fetch_tmdb_details(tmdb_id):
    base_url = "https://api.themoviedb.org/3"

    # 1. Basic Details
    details = requests.get(f"{base_url}/movie/{tmdb_id}", params={"api_key": TMDB_API_KEY, "language": "en-US"}).json()
    time.sleep(DELAY_BETWEEN_CALLS)

    # 2. Credits (Director/Cast)
    credits = requests.get(f"{base_url}/movie/{tmdb_id}/credits", params={"api_key": TMDB_API_KEY}).json()
    time.sleep(DELAY_BETWEEN_CALLS)

    # 3. Release Dates (Certification Fix Applied Here)
    release_resp = requests.get(f"{base_url}/movie/{tmdb_id}/release_dates", params={"api_key": TMDB_API_KEY}).json()
    cert_code = "NR"
    
    # Logic: Find US entry, then look for the first non-empty certification
    for entry in release_resp.get("results", []):
        if entry["iso_3166_1"] == "US":
            for date in entry.get("release_dates", []):
                # We check if the certification string is not empty
                if date.get("certification"):
                    cert_code = date["certification"]
                    break
            # If we found a cert, stop checking other countries (if any matched US)
            if cert_code != "NR":
                break
    time.sleep(DELAY_BETWEEN_CALLS)

    # 4. Watch Providers
    stream_resp = requests.get(f"{base_url}/movie/{tmdb_id}/watch/providers", params={"api_key": TMDB_API_KEY}).json()
    streaming_data = stream_resp.get("results", {}).get("US", {})
    streaming_info = []
    for key in ["flatrate", "rent", "buy"]:
        if key in streaming_data:
            streaming_info.extend([p["provider_name"] for p in streaming_data[key]])
    time.sleep(DELAY_BETWEEN_CALLS)

    # 5. Similar Movies
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
    try:
        videos = requests.get(f"https://api.themoviedb.org/3/movie/{tmdb_id}/videos", params={"api_key": TMDB_API_KEY}).json().get("results", [])
        for vid in videos:
            if vid["site"] == "YouTube" and vid["type"] == "Trailer":
                return f"https://www.youtube.com/watch?v={vid['key']}"
    except:
        return None
    return None

# --- AI ENRICHMENT (PROMPT UNCHANGED) ---
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
        logger.error(f"⚠️ OpenRouter fail: {e}")
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

        # AI Generation Strategy
        metadata = generate_via_ollama(movie_data)
        if not metadata:
            metadata = generate_via_openrouter(movie_data)
        
        if not metadata:
            logger.error(f"ID {tmdb_id}: AI generation failed.")
            return None

        # Data Cleaning
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
    input_file = "data/cleaned_movies.csv"
    
    if not os.path.exists(input_file):
        logger.error(f"File not found: {input_file}")
        exit()

    logger.info("Loading dataset...")
    df = pd.read_csv(input_file)
    
    # 1. Sort and limit (Adjust head() as needed)
    df = df.sort_values(by='popularity', ascending=False).head(5000).copy()
    
    # 2. Filter out already processed IDs
    existing_ids_query = cursor.execute("SELECT tmdb_id FROM movies").fetchall()
    existing_ids = set(row[0] for row in existing_ids_query)
    
    id_col = 'id' if 'id' in df.columns else 'tmdb_id'
    all_ids = df[id_col].tolist()
    ids_to_process = [tid for tid in all_ids if tid not in existing_ids]

    logger.info(f"Total: {len(all_ids)} | Done: {len(existing_ids)} | Queue: {len(ids_to_process)}")

    # 3. Process with Progress Bar (tqdm)
    for tid in tqdm(ids_to_process, desc="Enriching Movies", unit="film"):
        enrich_and_save(tid)
            
    logger.info("Batch processing complete.")
    conn.close()