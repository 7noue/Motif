import pandas as pd
import ollama
import requests
import sqlite3
import time
from tqdm import tqdm
from dotenv import load_dotenv
import os 
import json

# --- CONFIGURATION ---
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
if not TMDB_API_KEY:
    raise ValueError("❌ Missing TMDB_API_KEY.")

# --- STEP 1: LOAD DATA ---
input_file = "data/cleaned_movies.csv" 
df = pd.read_csv(input_file)

# For testing, we limit to 100. For production, remove .head(100)
df = df.sort_values(by='popularity', ascending=False).head(100).copy()
print(f"✅ Loaded {len(df)} movies.")

# --- STEP 2: DATABASE CACHE ---
def init_cache():
    conn = sqlite3.connect('motif_assets.db')
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
            producer TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_cache()

# --- STEP 3: API FETCHING ---
def fetch_tmdb_assets(movie_id):
    conn = sqlite3.connect('motif_assets.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM assets WHERE movie_id=?", (movie_id,))
    cached = cursor.fetchone()
    conn.close()

    if cached:
        # Return everything except the ID (indices 1 to 8)
        return cached[1], cached[2], cached[3], cached[4], cached[5], cached[6], cached[7], cached[8]

    try:
        # 1. Details
        url_details = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
        data = requests.get(url_details).json()
        poster_path = data.get('poster_path')
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""

        # 2. Videos
        url_videos = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={TMDB_API_KEY}"
        video_data = requests.get(url_videos).json()
        results = video_data.get('results', [])
        trailer_key = next((v['key'] for v in results if v['site'] == 'YouTube' and v['type'] == 'Trailer'), None)
        trailer_url = f"https://www.youtube.com/watch?v={trailer_key}" if trailer_key else ""

        # 3. Credits
        url_credits = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={TMDB_API_KEY}"
        credits_data = requests.get(url_credits).json()
        crew = credits_data.get('crew', [])
        cast_list = credits_data.get('cast', [])

        top_cast = [m['name'] for m in cast_list[:6]]
        cast_str = ", ".join(top_cast)

        directors = [m['name'] for m in crew if m['job'] == 'Director']
        director_str = ", ".join(directors)

        writers = [m['name'] for m in crew if m['job'] in ['Screenplay', 'Writer', 'Story']]
        writers = list(dict.fromkeys(writers))
        writer_str = ", ".join(writers[:3])

        cines = [m['name'] for m in crew if m['job'] == 'Director of Photography']
        cine_str = ", ".join(cines)

        composers = [m['name'] for m in crew if m['job'] == 'Original Music Composer']
        composer_str = ", ".join(composers)

        producers = [m['name'] for m in crew if m['job'] == 'Producer']
        producer_str = ", ".join(producers[:3])

        # Cache it
        conn = sqlite3.connect('motif_assets.db')
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO assets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                       (movie_id, poster_url, trailer_url, director_str, cast_str, writer_str, cine_str, composer_str, producer_str))
        conn.commit()
        conn.close()
        
        time.sleep(0.1)
        return poster_url, trailer_url, director_str, cast_str, writer_str, cine_str, composer_str, producer_str

    except Exception as e:
        print(f"Error {movie_id}: {e}")
        return "", "", "", "", "", "", "", ""

def generate_vibes_batch(batch_df):
    movies_text = ""
    for idx, row in batch_df.iterrows():
        movies_text += (
            f"ID: {row['id']} | "
            f"Movie: {row['title']} ({row.get('year', '')}) | "
            f"Overview: {row['overview']}\n---\n"
        )

    # 🔥 UPDATED PROMPT: INJECTING "CHRONICALLY ONLINE" KEYWORDS
    prompt = f"""
    You are a cultural historian of the internet.
    I will give you a list of movies. 
    
    For EACH movie, write a "Vibe" (max 60 words) that connects the film to MODERN INTERNET CULTURE.

    Your Vibe MUST include:
    1. **The Archetype:** Does this fit a specific internet subculture? (e.g., "Sigma Male", "Femcel", "Doomer", "Coquette", "Dark Academia", "Literally Me").
    2. **The Aesthetic:** (e.g., "Neon-noir", "Liminal space", "Cottagecore", "Y2K grit").
    3. **The Context:** When/Who to watch with (e.g., "3 AM doomscrolling", "For the girls", "Gym motivation").

    Examples:
    - Fight Club -> "The original Sigma Male manifesto. Toxic masculinity, consumerist rage, and gym motivation. The ultimate 'Literally Me' film for 3 AM doomscrolling."
    - Marie Antoinette -> "Peak Coquette aesthetic. Sofia Coppola's pastel dream. Sad girl luxury and indie sleaze. Perfect for a girls' night in."
    - Blade Runner 2049 -> "Lonely Doomer sci-fi. Holographic girlfriends and orange deserts. The definitive 'I look like this so I can feel like this' movie."

    Output Format (Strict JSON List):
    [
        {{"id": 12345, "vibe": "..."}},
        {{"id": 67890, "vibe": "..."}}
    ]

    Input Movies:
    {movies_text}
    """
    
    try:
        response = ollama.chat(model="llama3.1", messages=[{'role': 'user', 'content': prompt}], format='json')
        return json.loads(response['message']['content'])
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return []
    
# --- EXECUTION ---
tqdm.pandas()
print("⬇️ Fetching TMDB Assets...")
df[['poster_url', 'trailer_url', 'director', 'cast', 'writer', 'cinematographer', 'composer', 'producer']] = df['id'].progress_apply(
    lambda x: pd.Series(fetch_tmdb_assets(x))
)

print("🧠 Generating Vibes (Ollama)...")
batch_size = 1 # Keep low for safety
results_map = {}
chunks = [df[i:i + batch_size] for i in range(0, df.shape[0], batch_size)]

for chunk in tqdm(chunks):
    batch_results = generate_vibes_batch(chunk)
    if batch_results:
        if isinstance(batch_results, dict): batch_results = [batch_results]
        for item in batch_results:
            item_id = item.get('id') or item.get('ID')
            item_vibe = item.get('vibe') or item.get('Vibe')
            if item_id: results_map[item_id] = item_vibe
    
    # Checkpoint every 50 to avoid data loss
    if len(results_map) % 50 == 0:
        temp_df = df.copy()
        temp_df['synthetic_vibe'] = temp_df['id'].map(results_map)
        temp_df.to_csv("motif_checkpoint.csv", index=False)

# Final Map
df['synthetic_vibe'] = df['id'].map(results_map).fillna("")

# SAVE THE RAW MASTER DATA
df.to_csv("motif_master_data_100.csv", index=False)
print("✅ DONE! Raw data saved to 'motif_master_data_100.csv'. Now run Script 2.")