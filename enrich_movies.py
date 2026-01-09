import pandas as pd
from google import genai
import requests
import sqlite3
import time
from tqdm import tqdm
from dotenv import load_dotenv
import os 

# --- CONFIGURATION ---
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

if not GEMINI_API_KEY or not TMDB_API_KEY:
    raise ValueError("❌ Missing API Keys. Please check your .env file.")

# Initialize client with stripped key to avoid whitespace errors
client = genai.Client(api_key=GEMINI_API_KEY.strip())

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

def generate_synthetic_vibe(row):
    """
    Uses Gemini to create a 'Hybrid Vibe' (Scenario + Aesthetic).
    Captures precisely 'What it feels like' AND 'What it looks like'.
    """
    prompt = f"""
    You are a 'Vibe Curator' for a film app.
    Movie: {row['title']}
    Genres: {row.get('genres_str', 'Unknown')}
    Overview: {row['overview']}
    
    Task: Write a "Hybrid Vibe" description (max 50 words).
    Combine TWO elements:
    1. The Scenario: Social setting, mental state, or specific "use case" (e.g. "comfort watch", "trippy late-night", "good cry").
    2. The Aesthetic: Visual style, atmosphere, pacing, or texture (e.g. "warm 70s grain", "neon-noir", "snowy isolation").

    Constraints:
    - Do NOT describe the plot.
    - Use comma-separated adjectives and short phrases ONLY.
    - Focus on the HUMAN context (Who, When, Why) and the VISUAL style.
    - Avoid generic praise like "masterpiece" or "must-watch".
    
    Example Output: "Mind-bending late-night trip, neon-soaked noir visuals, existential dread, deep focus atmosphere, slow-burn tension, visually hypnotic."
    """
    
    max_retries = 3
    base_wait_time = 4.0 # 4 seconds = 15 RPM (Safe zone)

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-lite", 
                contents=prompt
            )
            time.sleep(base_wait_time)
            return response.text.strip()
            
        except Exception as e:
            error_msg = str(e)
            # Handle Rate Limits (429)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                print(f"\n⏳ Hit Rate Limit on '{row['title']}'. Cooling down for 65s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(65) # Wait out the full minute
                continue 
            else:
                print(f"⚠️ Error generating vibe for {row['title']}: {e}")
                return ""
    
    return "" # Return empty if all retries fail

def sanity_check(df):
    print("\n--- 🧐 RUNNING SANITY CHECK ---")
    empty_vibes = df[df['synthetic_vibe'].isna() | (df['synthetic_vibe'] == "")]
    success_count = len(df) - len(empty_vibes)
    print(f"📊 Vibe Generation Stats: {success_count}/{len(df)} successful.")
    
    print("\n--- 👁️ VISUAL SAMPLE (First 2 Rows) ---")
    for index, row in df.head(2).iterrows():
        print(f"🎬 Title: {row['title']}")
        print(f"✨ Vibe:  {row['synthetic_vibe'][:120]}...") 
        print(f"🔗 Poster: {row['poster_url']}")
        print("-" * 40)

# --- STEP 4: EXECUTION LOOP ---
print("🚀 Starting enrichment... (Running at safe speed to avoid errors)")
tqdm.pandas() 

print(" ⬇️ Fetching/Loading Assets (Hybrid Cache)...")
df[['poster_url', 'trailer_url']] = df['id'].progress_apply(
    lambda x: pd.Series(fetch_tmdb_assets(x))
)

print(" 🧠 Generating Hybrid Vibes (Scenario + Aesthetic)...")
df['synthetic_vibe'] = df.progress_apply(generate_synthetic_vibe, axis=1)

# Create final string for Vector Search
df['rag_content'] = (
    "Title: " + df['title'].astype(str) + ". " +
    "Vibe: " + df['synthetic_vibe'].astype(str) + ". " +
    "Genres: " + df.get('genres_str', pd.Series([''] * len(df))).astype(str) + ". " +
    "Keywords: " + df.get('keywords_str', pd.Series([''] * len(df))).astype(str)
)

sanity_check(df)

# --- STEP 5: SAVE ---
output_file = "motif_mvp_100.csv"
df.to_csv(output_file, index=False)
print(f"✅ DONE! Saved enriched data to {output_file}")