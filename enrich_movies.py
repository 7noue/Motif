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

# We only need TMDB Key now, Gemini Key is removed
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

if not TMDB_API_KEY:
    raise ValueError("❌ Missing TMDB_API_KEY. Please check your .env file.")

# --- STEP 1: LOAD DATA ---
input_file = "data/cleaned_movies.csv"
if not os.path.exists(input_file):
    print(f"❌ Error: Could not find {input_file}")
    exit()

print("📂 Loading dataset...")
df = pd.read_csv(input_file)
# Filter to top 100
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
    """Fetches live data from TMDB API if not in cache"""
    # Check Cache
    conn = sqlite3.connect('motif_assets.db')
    cursor = conn.cursor()
    cursor.execute("SELECT poster_url, trailer_url FROM assets WHERE movie_id=?", (movie_id,))
    cached = cursor.fetchone()
    conn.close()

    if cached:
        return cached[0], cached[1]

    # API Call
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

        # Save to cache
        conn = sqlite3.connect('motif_assets.db')
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO assets VALUES (?, ?, ?)", (movie_id, poster_url, trailer_url))
        conn.commit()
        conn.close()
        
        time.sleep(0.2) 
        return poster_url, trailer_url
    except Exception as e:
        print(f"⚠️ Error fetching assets for ID {movie_id}: {e}")
        return "", ""

def generate_vibes_batch(batch_df):
    """
    Sends a batch to Local Ollama (Llama 3.1).
    """
    # 1. Format the input list
    movies_text = ""
    for idx, row in batch_df.iterrows():
        movies_text += (
            f"ID: {row['id']} | "
            f"Movie: {row['title']} | "
            f"Genres: {row.get('genres_str', 'Unknown')} | "
            f"Overview: {row['overview']}\n---\n"
        )

    # 2. Your Exact Prompt Logic
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
    - Avoid generic praise like "masterpiece" or "must-watch".
    
    Input Movies:
    {movies_text}

    Output Format (Strict JSON List):
    [
        {{"id": 12345, "vibe": "Mind-bending late-night trip, neon-soaked noir visuals, existential dread..."}},
        {{"id": 67890, "vibe": "Warm 90s nostalgia, comfort watch, golden hour cinematography..."}}
    ]
    """
    
    try:
        # CALL OLLAMA LOCALLY
        # format='json' enforces valid JSON output (supported by Llama 3.1)
        response = ollama.chat(
            model="llama3.1", 
            messages=[{'role': 'user', 'content': prompt}],
            format='json'
        )
        
        content = response['message']['content']
        return json.loads(content)

    except Exception as e:
        print(f"⚠️ Batch failed: {e}")
        return []

def sanity_check(df):
    print("\n--- 🧐 RUNNING SANITY CHECK ---")
    empty_vibes = df[df['synthetic_vibe'].isna() | (df['synthetic_vibe'] == "")]
    success_count = len(df) - len(empty_vibes)
    print(f"📊 Vibe Generation Stats: {success_count}/{len(df)} successful.")
    
    print("\n--- 👁️ VISUAL SAMPLE (First 2 Rows) ---")
    for index, row in df.head(2).iterrows():
        print(f"🎬 Title: {row['title']}")
        print(f"✨ Vibe:   {str(row['synthetic_vibe'])[:120]}...") 
        print(f"🔗 Poster: {row['poster_url']}")
        print("-" * 40)

# --- STEP 4: EXECUTION LOOP ---
print("🚀 Starting enrichment... (Running efficiently in Batches of 1 for GPU safety)")
tqdm.pandas() 

print(" ⬇️ Fetching/Loading Assets (Hybrid Cache)...")
df[['poster_url', 'trailer_url']] = df['id'].progress_apply(
    lambda x: pd.Series(fetch_tmdb_assets(x))
)

print(" 🧠 Generating Hybrid Vibes (Scenario + Aesthetic)...")

# --- BATCH PROCESSING START ---
# CHANGED TO 1: To prevent VRAM overflow on GTX 1660 Super
batch_size = 1
results_map = {}

# Break DF into chunks
chunks = [df[i:i + batch_size] for i in range(0, df.shape[0], batch_size)]

for chunk in tqdm(chunks):
    batch_results = generate_vibes_batch(chunk)
    
    if batch_results:
        # Check if result is a list (expected) or dict (sometimes happens with single batch)
        if isinstance(batch_results, dict):
            batch_results = [batch_results]
            
        for item in batch_results:
            # Flexible key access in case LLM capitalizes 'ID'
            item_id = item.get('id') or item.get('ID')
            item_vibe = item.get('vibe') or item.get('Vibe')
            
            if item_id:
                results_map[item_id] = item_vibe
    else:
        print("⚠️ Warning: Skipped a batch.")
    
    # CHECKPOINT SAVING
    df['synthetic_vibe'] = df['id'].map(results_map)
    df.to_csv("motif_mvp_100_CHECKPOINT.csv", index=False)

# Apply results to main DataFrame
df['synthetic_vibe'] = df['id'].map(results_map)
df['synthetic_vibe'] = df['synthetic_vibe'].fillna("") 
# --- BATCH PROCESSING END ---

# Create final string for Vector Search
df['rag_content'] = (
    "Title: " + df['title'].astype(str) + ". " +
    "Vibe: " + df['synthetic_vibe'].astype(str) + ". " +
    "Genres: " + df.get('genres_str', pd.Series([''] * len(df))).astype(str) + ". " +
    "Keywords: " + df.get('keywords_str', pd.Series([''] * len(df))).astype(str)
)

sanity_check(df)

# --- STEP 5: SAVE ---
output_file = "motif_mvp_100_local.csv"
df.to_csv(output_file, index=False)
print(f"✅ DONE! Saved enriched data to {output_file}")