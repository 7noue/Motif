import pandas as pd
import requests
import sqlite3
import time
from tqdm import tqdm
from dotenv import load_dotenv
import os 

# --- CONFIGURATION ---
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

if not TMDB_API_KEY:
    raise ValueError("❌ Missing TMDB_API_KEY.")

# --- PATH SETUP ---
# Get the folder where THIS script lives (backend/scripts)
script_dir = os.path.dirname(os.path.abspath(__file__))

# 1. Path to CSV (backend/data/motif_master_data_100.csv)
csv_path = os.path.join(script_dir, "../data/motif_master_data_100.csv")

# 2. Path to DB (backend/data/motif_assets.db)
# FIX: Point to the 'data' folder, not the 'scripts' folder
db_path = os.path.join(script_dir, "../data/motif_assets.db")

if not os.path.exists(csv_path):
    raise FileNotFoundError(f"❌ Could not find CSV at {csv_path}. Run Script 1 first!")

print(f"📂 Loading master data: {csv_path}...")
df = pd.read_csv(csv_path)

# --- STEP 2: DEFINE CHARACTER FETCHER ---
def fetch_rich_cast(movie_id):
    """
    Fetches cast AND character names.
    Returns: "Actor Name (as Character Name)"
    """
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={TMDB_API_KEY}"
        data = requests.get(url).json()
        cast_list = data.get('cast', [])

        rich_cast = []
        for member in cast_list[:8]: # Grab top 8
            name = member.get('name', '')
            char = member.get('character', '').strip()
            
            # Filter out "Himself", "Uncredited" noise
            if char and not any(x in char.lower() for x in ['uncredited', 'himself', 'herself']):
                 rich_cast.append(f"{name} (as {char})")
            else:
                 rich_cast.append(name)
        
        return ", ".join(rich_cast)
    except Exception as e:
        print(f"⚠️ Error fetching {movie_id}: {e}")
        return ""

# --- STEP 3: RUN THE PATCH ---
print("🕵️‍♀️ Fetching Character Names (Patching)...")
tqdm.pandas()

# Apply the new fetcher
df['cast'] = df['id'].progress_apply(fetch_rich_cast)

# --- STEP 4: SAVE CSV (Do this FIRST so we don't lose data) ---
df.to_csv(csv_path, index=False)
print(f"✅ CSV UPDATED! Saved to: {csv_path}")

# --- STEP 5: UPDATE DATABASE (Optional Cache Update) ---
print(f"💾 Updating Local Cache at {db_path}...")
try:
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists first
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='assets';")
        if cursor.fetchone():
            data_to_update = list(zip(df['cast'], df['id']))
            cursor.executemany("UPDATE assets SET cast = ? WHERE movie_id = ?", data_to_update)
            conn.commit()
            print("✅ Database cache updated successfully.")
        else:
            print("⚠️ 'assets' table not found in DB. Skipping cache update (CSV is safe).")
        
        conn.close()
    else:
        print("⚠️ Database file not found. Skipping cache update (CSV is safe).")

except Exception as e:
    print(f"⚠️ Warning: Could not update database cache ({e}), but CSV is saved!")

print("\n🚀 SUCCESS! Now run 'python backend/scripts/2_construct_rag.py' to rebuild the RAG strings.")