import pandas as pd
import ollama
import requests
import sqlite3
import time
from tqdm import tqdm
from dotenv import load_dotenv
import os
import json
from contextlib import closing
import logging

# --- CONFIGURATION & LOGGING ---
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
if not TMDB_API_KEY:
    raise ValueError("❌ Missing TMDB_API_KEY.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- STEP 1: LOAD DATA ---
input_file = "data/cleaned_movies.csv"
df = pd.read_csv(input_file)

# For testing, we limit to 100. For production, remove .head(100)
df = df.sort_values(by='popularity', ascending=False).head(100).copy()
logger.info(f"✅ Loaded {len(df)} movies.")

# --- STEP 2: ENHANCED DATABASE CACHE ---
def init_cache():
    """Initialize SQLite cache with connection pooling approach"""
    conn = sqlite3.connect('motif_assets.db', check_same_thread=False)
    conn.execute('PRAGMA journal_mode=WAL')  # Better concurrency
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS assets (
        movie_id INTEGER PRIMARY KEY,
        poster_url TEXT,
        trailer_url TEXT,
        director TEXT,
        cast TEXT,
        writer TEXT,
        cinematographer TEXT,
        composer TEXT,
        producer TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create vibe cache table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vibes_cache (
        movie_id INTEGER PRIMARY KEY,
        vibe TEXT,
        tags TEXT,
        model_used TEXT,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    return conn  # Return connection for reuse

# Initialize single connection for the session
cache_conn = init_cache()

def fetch_tmdb_assets(movie_id):
    """Enhanced TMDB asset fetcher with better caching and error handling"""
    cursor = cache_conn.cursor()
    cursor.execute("SELECT * FROM assets WHERE movie_id=?", (movie_id,))
    cached = cursor.fetchone()
    
    if cached:
        # Return everything except the ID (indices 1 to 8)
        return cached[1], cached[2], cached[3], cached[4], cached[5], cached[6], cached[7], cached[8]
    
    try:
        # 1. Details
        url_details = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
        response = requests.get(url_details, timeout=10)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get('poster_path')
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""
        
        # 2. Videos
        url_videos = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={TMDB_API_KEY}"
        video_response = requests.get(url_videos, timeout=10)
        video_response.raise_for_status()
        video_data = video_response.json()
        results = video_data.get('results', [])
        trailer_key = next((v['key'] for v in results if v['site'] == 'YouTube' and v['type'] == 'Trailer'), None)
        trailer_url = f"https://www.youtube.com/watch?v={trailer_key}" if trailer_key else ""
        
        # 3. Credits with enhanced rich cast logic
        url_credits = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={TMDB_API_KEY}"
        credits_response = requests.get(url_credits, timeout=10)
        credits_response.raise_for_status()
        credits_data = credits_response.json()
        crew = credits_data.get('crew', [])
        cast_list = credits_data.get('cast', [])
        
        # --- ENHANCED RICH CAST LOGIC ---
        rich_cast = []
        for member in cast_list[:8]:  # Grab top 8
            name = member.get('name', '')
            char = member.get('character', '').strip()
            
            # Enhanced filtering with more noise patterns
            if char and not any(x in char.lower() for x in ['uncredited', 'himself', 'herself', 'voice', 'narrator', 'archive']):
                # Clean character name (remove parentheses content)
                char_clean = char.split('(')[0].strip()
                if char_clean and len(char_clean) < 50:  # Avoid overly long character names
                    rich_cast.append(f"{name} (as {char_clean})")
                else:
                    rich_cast.append(name)
            elif name:
                rich_cast.append(name)
        
        cast_str = ", ".join(rich_cast[:6])  # Limit to 6 for readability
        
        # Crew extraction with deduplication
        directors = list(dict.fromkeys([m['name'] for m in crew if m['job'] == 'Director']))
        director_str = ", ".join(directors[:2])
        
        writers = list(dict.fromkeys([m['name'] for m in crew if m['job'] in ['Screenplay', 'Writer', 'Story', 'Novel']]))
        writer_str = ", ".join(writers[:3])
        
        cines = list(dict.fromkeys([m['name'] for m in crew if m['job'] == 'Director of Photography']))
        cine_str = ", ".join(cines[:2])
        
        composers = list(dict.fromkeys([m['name'] for m in crew if m['job'] == 'Original Music Composer']))
        composer_str = ", ".join(composers[:2])
        
        producers = list(dict.fromkeys([m['name'] for m in crew if m['job'] == 'Producer']))
        producer_str = ", ".join(producers[:3])
        
        # Cache it
        cursor.execute("""
            INSERT OR REPLACE INTO assets 
            (movie_id, poster_url, trailer_url, director, cast, writer, cinematographer, composer, producer)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (movie_id, poster_url, trailer_url, director_str, cast_str, writer_str, cine_str, composer_str, producer_str))
        cache_conn.commit()
        
        time.sleep(0.12)  # Slightly increased delay to respect rate limits
        return poster_url, trailer_url, director_str, cast_str, writer_str, cine_str, composer_str, producer_str
        
    except requests.exceptions.RequestException as e:
        logger.error(f"TMDB API Error for movie {movie_id}: {e}")
        return "", "", "", "", "", "", "", ""
    except Exception as e:
        logger.error(f"Unexpected error for movie {movie_id}: {e}")
        return "", "", "", "", "", "", "", ""

def generate_vibes_batch(batch_df):
    """
    Enhanced God-Tier Semantic Architect Prompt with structured output.
    Optimized batch processing for better contrast and throughput.
    """
    movies_text = ""
    for idx, row in batch_df.iterrows():
        movies_text += (
            f"<FILM_{idx + 1}>\n"
            f"TMDB_ID: {row['id']}\n"
            f"TITLE: {row['title']}\n"
            f"PLOT_SUMMARY: {row['overview'][:500] if pd.notna(row['overview']) else 'No summary'}\n"
            f"</FILM_{idx + 1}>\n\n"
        )
    
    prompt = f"""
### ROLE: PRECISE METADATA TAGGER & CULTURAL ARCHITECT

You are a specialized system that maps films to internet subculture vocabulary. Your output must be machine-parseable and culturally dense.

### OBJECTIVE
For each film, generate:
1. A "vibe" - 50-60 words of cultural positioning
2. A "tags" list - 6-10 specific tropes (NO adjectives)

### STRUCTURAL GUARDRAILS
- Vibe MUST contain exactly one PRIMARY ARCHETYPE from: [Sigma, Coquette, Doomer, Femcel, Dark Academia, Golden Retriever, Unhinged, Corecore, Literally Me, Good For Her, Liminal]
- Vibe MUST contain 2-3 AESTHETIC KEYWORDS from: [Synthwave, Cottagecore, Brutalist, Y2K, Neo-noir, Dreamcore, Old Money, Grunge]
- Vibe MUST include HUMAN CONTEXT: "for when..." or "perfect for..." scenario
- Tags MUST be HARD TROPES only: ['Unreliable Narrator', 'Slow Burn', 'Found Family', 'Body Horror', 'Heist', 'Coming-of-Age', 'Psychological Thriller', 'Gaslighting', 'Betrayal', 'Redemption Arc', 'Anti-Hero', 'Fish Out of Water']

### COGNITIVE PROCESS
1. Identify dominant cultural archetype
2. Extract visual/sonic aesthetic DNA
3. Identify key scenes/dialogue that became iconic or memes
4. List narrative tropes without judgment

### OUTPUT FORMAT (STRICT JSON)
{{
    "films": [
        {{
            "id": <TMDB_ID>,
            "vibe": "<50-60 word cultural summary>",
            "tags": ["trope1", "trope2", ...]
        }}
    ]
}}

### FILMS TO PROCESS
{movies_text}

### FINAL INSTRUCTIONS
- Return ONLY the JSON object
- NO markdown, NO explanations
- Ensure each film has EXACTLY one entry
- Tags must be 6-10 items, comma-separated in the list
- If unsure about internet lore, focus on atmospheric vibe and tropes
"""

    try:
        response = ollama.chat(
            model="llama3.1",
            messages=[{'role': 'user', 'content': prompt}],
            format='json',
            options={'temperature': 0.3}  # Lower temp for consistency
        )
        
        result = json.loads(response['message']['content'])
        
        # Validate structure
        if 'films' not in result:
            logger.warning("Unexpected response structure, attempting to parse")
            # Try to handle different possible structures
            if isinstance(result, list):
                return result
            elif 'id' in result:
                return [result]
            else:
                return []
        
        return result['films']
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}\nResponse was: {response.get('message', {}).get('content', '')[:200]}")
        return []
    except Exception as e:
        logger.error(f"Ollama generation error: {e}")
        return []

def cache_vibe_result(movie_id, vibe, tags):
    """Cache generated vibe results to avoid reprocessing"""
    cursor = cache_conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO vibes_cache 
        (movie_id, vibe, tags, model_used)
        VALUES (?, ?, ?, ?)
    """, (movie_id, vibe, tags, 'llama3.1'))
    cache_conn.commit()

def get_cached_vibe(movie_id):
    """Retrieve cached vibe if exists"""
    cursor = cache_conn.cursor()
    cursor.execute("SELECT vibe, tags FROM vibes_cache WHERE movie_id=?", (movie_id,))
    result = cursor.fetchone()
    return (result[0], result[1]) if result else (None, None)

# --- EXECUTION ---
def main():
    print("⬇️ Fetching TMDB Assets...")
    
    # Apply with progress bar
    asset_columns = ['poster_url', 'trailer_url', 'director', 'cast', 'writer', 
                    'cinematographer', 'composer', 'producer']
    
    # Use vectorized approach where possible
    tqdm.pandas(desc="Fetching assets")
    
    # Process assets
    assets_data = []
    for movie_id in tqdm(df['id'].values, desc="TMDB API"):
        assets = fetch_tmdb_assets(movie_id)
        assets_data.append(assets)
    
    # Assign to DataFrame
    df[asset_columns] = assets_data
    
    print("🧠 Generating Vibes (Enhanced Batch Processing)...")
    
    # Optimized batch processing (3 films per batch for better contrast)
    batch_size = 3
    results_map = {}
    tags_map = {}
    
    # Check cache first
    for movie_id in df['id'].values:
        cached_vibe, cached_tags = get_cached_vibe(movie_id)
        if cached_vibe and cached_tags:
            results_map[movie_id] = cached_vibe
            tags_map[movie_id] = cached_tags
    
    # Get remaining movies to process
    remaining_ids = set(df['id'].values) - set(results_map.keys())
    remaining_df = df[df['id'].isin(remaining_ids)]
    
    if not remaining_df.empty:
        chunks = [remaining_df[i:i + batch_size] for i in range(0, len(remaining_df), batch_size)]
        
        for chunk_idx, chunk in enumerate(tqdm(chunks, desc="Generating vibes")):
            logger.info(f"Processing batch {chunk_idx + 1}/{len(chunks)} with {len(chunk)} films")
            
            batch_results = generate_vibes_batch(chunk)
            
            if batch_results:
                for item in batch_results:
                    item_id = item.get('id')
                    item_vibe = item.get('vibe')
                    item_tags = item.get('tags')
                    
                    if item_id and item_vibe:
                        # Convert tags list to string for storage
                        if isinstance(item_tags, list):
                            tags_str = json.dumps(item_tags)
                        else:
                            tags_str = str(item_tags)
                        
                        results_map[item_id] = item_vibe
                        tags_map[item_id] = tags_str
                        
                        # Cache for future use
                        cache_vibe_result(item_id, item_vibe, tags_str)
            
            # Checkpoint every 3 batches
            if (chunk_idx + 1) % 3 == 0:
                temp_df = df.copy()
                temp_df['synthetic_vibe'] = temp_df['id'].map(results_map)
                temp_df['tags'] = temp_df['id'].map(tags_map)
                temp_df.to_csv("motif_checkpoint.csv", index=False)
                logger.info(f"Checkpoint saved after batch {chunk_idx + 1}")
    
    # Map results to DataFrame
    df['synthetic_vibe'] = df['id'].map(results_map).fillna("")
    df['tags'] = df['id'].map(tags_map).fillna("[]")
    
    # Convert tags from string to list for consistency
    df['tags'] = df['tags'].apply(lambda x: json.loads(x) if isinstance(x, str) and x.startswith('[') else [])
    
    # SAVE THE RAW MASTER DATA
    output_file = "motif_master_data_100.csv"
    df.to_csv(output_file, index=False)
    
    # Close database connection
    cache_conn.close()
    
    print(f"✅ DONE! Raw data saved to '{output_file}'.")
    print(f"✅ Generated {len(results_map)} vibes ({len(tags_map)} tag sets).")
    print("✅ Now run Script 2 to build RAG strings.")

if __name__ == "__main__":
    main()