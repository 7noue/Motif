import os
import json
import time
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

# --- TMDB HELPERS ---
def fetch_tmdb_details(tmdb_id):
    """Fetch movie data, certifications, streaming info, and language."""
    base_url = "https://api.themoviedb.org/3"

    # 1. Movie Details
    details_resp = requests.get(
        f"{base_url}/movie/{tmdb_id}",
        params={"api_key": TMDB_API_KEY, "language": "en-US"}
    )
    details = details_resp.json()
    time.sleep(DELAY_BETWEEN_CALLS)

    # 2. Credits
    credits_resp = requests.get(f"{base_url}/movie/{tmdb_id}/credits", params={"api_key": TMDB_API_KEY})
    credits = credits_resp.json()
    time.sleep(DELAY_BETWEEN_CALLS)

    # 3. Certifications
    release_resp = requests.get(f"{base_url}/movie/{tmdb_id}/release_dates", params={"api_key": TMDB_API_KEY})
    releases = release_resp.json()
    cert_code = "NR"
    for entry in releases.get("results", []):
        if entry["iso_3166_1"] == "US" and entry["release_dates"]:
            cert_code = entry["release_dates"][0].get("certification", "NR")
            break
    time.sleep(DELAY_BETWEEN_CALLS)

    # 4. Streaming providers
    stream_resp = requests.get(f"{base_url}/movie/{tmdb_id}/watch/providers", params={"api_key": TMDB_API_KEY})
    stream_data = stream_resp.json().get("results", {}).get("US", {})
    streaming_info = []
    for key in ["flatrate", "rent", "buy"]:
        if key in stream_data:
            streaming_info.extend([p["provider_name"] for p in stream_data[key]])
    time.sleep(DELAY_BETWEEN_CALLS)

    # 5. Similar films
    similar_resp = requests.get(f"{base_url}/movie/{tmdb_id}/similar", params={"api_key": TMDB_API_KEY, "language": "en-US"})
    similar_movies = [m["title"] for m in similar_resp.json().get("results", [])[:MAX_SIMILAR_FILMS]]
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
    base_url = "https://api.themoviedb.org/3"
    videos_resp = requests.get(f"{base_url}/movie/{tmdb_id}/videos", params={"api_key": TMDB_API_KEY})
    videos = videos_resp.json().get("results", [])
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

# --- ENRICH AND RETURN ---
def enrich_movie(tmdb_id):
    movie_data = fetch_tmdb_details(tmdb_id)

    # AI metadata (try Ollama first, fallback OpenRouter)
    metadata = generate_via_ollama(movie_data) or generate_via_openrouter(movie_data) or {}

    # Vibe signature percent correction
    vibe_val = metadata.get("vibe_signature", {}).get("val_percent", 0)
    metadata["vibe_signature"]["val_percent"] = min(max(vibe_val, 0), 100)

    # Combine all enriched data
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

    return enriched_movie

# --- EXAMPLE REAL-TIME USAGE ---
if __name__ == "__main__":
    tmdb_ids = [603, 550, 680]  # Example TMDB IDs
    for tid in tmdb_ids:
        movie = enrich_movie(tid)
        print(json.dumps(movie, indent=2))
