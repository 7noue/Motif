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

# --- STEP 1: LOAD FULL DATA ---
input_file = "data/cleaned_movies.csv"
print("📂 Loading dataset...")
df = pd.read_csv(input_file)

# Filter to top 5000
df = df.sort_values(by='popularity', ascending=False).head(5000).copy()
print(f"✅ Filtered to top {len(df)} popular movies.")

# --- STEP 2: SETUP HYBRID CACHE ---
def init_cache():
    conn = sqlite3.connect('motif_assets.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            movie_id INTEGER PRIMARY KEY,
            poster_url TEXT,
            trailer_url TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_cache()

# --- STEP 3: HELPER FUNCTIONS ---
def fetch_tmdb_assets(movie_id):
    conn = sqlite3.connect('motif_assets.db')
    cursor = conn.cursor()
    cursor.execute("SELECT poster_url, trailer_url FROM assets WHERE movie_id=?", (movie_id,))
    cached = cursor.fetchone()
    conn.close()

    if cached:
        return cached[0], cached[1]

    try:
        url_details = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
        data = requests.get(url_details).json()
        poster_path = data.get('poster_path')
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""

        url_videos = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={TMDB_API_KEY}"
        video_data = requests.get(url_videos).json()
        results = video_data.get('results', [])
        trailer_key = next((v['key'] for v in results if v['site'] == 'YouTube' and v['type'] == 'Trailer'), None)
        trailer_url = f"https://www.youtube.com/watch?v={trailer_key}" if trailer_key else ""

        conn = sqlite3.connect('motif_assets.db')
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO assets VALUES (?, ?, ?)", (movie_id, poster_url, trailer_url))
        conn.commit()
        conn.close()
        
        time.sleep(0.2) 
        return poster_url, trailer_url
    except Exception as e:
        return "", ""

def generate_vibes_batch(batch_df):
    movies_text = ""
    for idx, row in batch_df.iterrows():
        movies_text += (
            f"ID: {row['id']} | "
            f"Movie: {row['title']} | "
            f"Genres: {row.get('genres_str', 'Unknown')} | "
            f"Overview: {row['overview']}\n---\n"
        )

    prompt = f"""
    You are a 'Vibe Curator' for a film app. I will give you a list of movies.
    
    For EACH movie, write a "Hybrid Vibe" description (max 50 words).
    
    Your Vibe MUST combine TWO elements:
    1. The Scenario: Social setting, mental state, or specific "use case" (e.g. "comfort watch", "trippy late-night", "good cry").
    2. The Aesthetic: Visual style, atmosphere, pacing, or texture (e.g. "warm 70s grain", "neon-noir", "snowy isolation").

    Constraints for every movie:
    - Do NOT describe the plot.
    - Use comma-separated adjectives and short phrases ONLY.
    - Focus on the HUMAN context (Who, When, Why) and the VISUAL style.
    
    Input Movies:
    {movies_text}

    Output Format (Strict JSON List):
    [
        {{"id": 12345, "vibe": "Mind-bending late-night trip, neon-soaked noir visuals..."}}
    ]
    """
    
    try:
        response = ollama.chat(
            model="llama3.1", 
            messages=[{'role': 'user', 'content': prompt}],
            format='json'
        )
        return json.loads(response['message']['content'])
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return []

# --- STEP 4: EXECUTION LOOP ---
print("🚀 Starting enrichment (5000 Movies) with Local Ollama...")
tqdm.pandas() 

print(" ⬇️ Fetching Assets...")
df[['poster_url', 'trailer_url']] = df['id'].progress_apply(
    lambda x: pd.Series(fetch_tmdb_assets(x))
)

print(" 🧠 Generating Hybrid Vibes...")

batch_size = 1
results_map = {}
chunks = [df[i:i + batch_size] for i in range(0, df.shape[0], batch_size)]

for chunk in tqdm(chunks):
    batch_results = generate_vibes_batch(chunk)
    
    if batch_results:
        if isinstance(batch_results, dict):
            batch_results = [batch_results]

        for item in batch_results:
            item_id = item.get('id') or item.get('ID')
            item_vibe = item.get('vibe') or item.get('Vibe')
            if item_id:
                results_map[item_id] = item_vibe
    
    # Save checkpoint every 50 movies (to avoid losing 8 hours of work)
    if len(results_map) % 50 == 0:
        df['synthetic_vibe'] = df['id'].map(results_map)
        df.to_csv("motif_mvp_5000_CHECKPOINT.csv", index=False)

df['synthetic_vibe'] = df['id'].map(results_map)
df['synthetic_vibe'] = df['synthetic_vibe'].fillna("")

df['rag_content'] = (
    "Title: " + df['title'].astype(str) + ". " +
    "Vibe: " + df['synthetic_vibe'].astype(str) + ". " +
    "Genres: " + df.get('genres_str', pd.Series([''] * len(df))).astype(str) + ". " +
    "Keywords: " + df.get('keywords_str', pd.Series([''] * len(df))).astype(str)
)

# --- STEP 5: SAVE ---
output_file = "motif_mvp_5000_local.csv"
df.to_csv(output_file, index=False)
print(f"✅ DONE! Saved 5000 movies to {output_file}")