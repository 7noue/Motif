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
input_file = "data/cleaned_movies.csv"  # Ensure this path is correct relative to where you run the script
print("📂 Loading dataset...")
df = pd.read_csv(input_file)

# --- CHANGED: Filter to top 100 ---
df = df.sort_values(by='popularity', ascending=False).head(100).copy()
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
    """
    Sends a batch to Local Ollama (Llama 3.1).
    Optimized for MEMES, POP CULTURE, and HUMAN CONTEXT (Occasions).
    """
    # 1. Format the input list
    movies_text = ""
    for idx, row in batch_df.iterrows():
        movies_text += (
            f"ID: {row['id']} | "
            f"Movie: {row['title']} ({row.get('year', '')}) | "
            f"Overview: {row['overview']}\n---\n"
        )

    # 2. The "Culture Vulture" Prompt (Updated for Context)
    prompt = f"""
    You are a blunt, internet-savvy film curator. 
    I will give you a list of movies. Use your OWN knowledge + the overview.

    For EACH movie, write a "Vibe" (max 60 words).

    Your Vibe MUST combine these 3 layers:
    1. The Aesthetic/Mood: (e.g., "Neon-noir", "Anxiety-inducing", "Cozy").
    2. The "Sauce": Iconic memes, quotes, or actor appeal (e.g., "Patrick Bateman's skincare routine", "The sheer audacity of Nic Cage").
    3. The "Human Context" (CRITICAL):
       - WHEN to watch: (e.g., "Christmas classic", "3 AM doomscrolling", "First date danger zone", "Sunday hangover cure").
       - WHO to watch with: (e.g., "Watch with the boys", "Strictly solo watch").
    
    ### ANTI-HALLUCINATION RULES:
    - If a movie is NOT associated with a specific holiday (like Christmas/Halloween), DO NOT invent one. Instead, use a setting like "Rainy afternoon" or "Late night".
    - Focus on how REAL people consume this content.

    Output Format (Strict JSON List):
    [
        {{"id": 12345, "vibe": "Pure anxiety and sweat-drenched jazz. J.K. Simmons screaming 'Not my tempo'. Perfect for when you need toxic motivation at 2 AM."}},
        {{"id": 67890, "vibe": "The ultimate Christmas movie, actually. Yippee Ki-Yay, ventilation ducts, and Bruce Willis in a tank top. Watch with dad and a beer."}},
        {{"id": 11223, "vibe": "Depressing but beautiful sci-fi. Ryan Gosling looks lonely in neon rain. Literally me. Strictly a 3 AM solo watch when you feel empty."}}
    ]

    Input Movies:
    {movies_text}
    """
    
    try:
        response = ollama.chat(
            model="llama3.1", 
            messages=[{'role': 'user', 'content': prompt}],
            format='json'
        )
        content = response['message']['content']
        return json.loads(content)

    except Exception as e:
        print(f"⚠️ Error: {e}")
        return []

# --- STEP 4: EXECUTION LOOP ---
print("🚀 Starting enrichment (100 Movies) with Local Ollama...")
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
    
    # --- CHANGED: Checkpoint every 10 movies (since we only have 100) ---
    if len(results_map) % 10 == 0:
        df['synthetic_vibe'] = df['id'].map(results_map)
        df.to_csv("motif_mvp_100_CHECKPOINT.csv", index=False)

df['synthetic_vibe'] = df['id'].map(results_map)
df['synthetic_vibe'] = df['synthetic_vibe'].fillna("")

df['rag_content'] = (
    "Title: " + df['title'].astype(str) + ". " +
    "Vibe: " + df['synthetic_vibe'].astype(str) + ". " +
    "Genres: " + df.get('genres_str', pd.Series([''] * len(df))).astype(str) + ". " +
    "Keywords: " + df.get('keywords_str', pd.Series([''] * len(df))).astype(str)
)

# --- STEP 5: SAVE ---
output_file = "motif_mvp_100_local.csv"
df.to_csv(output_file, index=False)
print(f"✅ DONE! Saved 100 movies to {output_file}")