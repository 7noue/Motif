import sqlite3
import requests
import os
import time
from dotenv import load_dotenv
from tqdm import tqdm  # <--- Added import

# --- SETUP ---
# FIX: Since this file is in 'backend/', the DB is in the same folder.
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(CURRENT_DIR, "movies.db")
ENV_PATH = os.path.join(CURRENT_DIR, "../.env") # Changed back to .env inside backend based on your file structure

load_dotenv(ENV_PATH)
TMDB_KEY = os.getenv("TMDB_API_KEY")

if not TMDB_KEY:
    print("❌ ERROR: Missing TMDB_API_KEY in .env file.")
    print("   -> Get one at https://www.themoviedb.org/settings/api")
    exit(1)

def get_db():
    # tqdm.write ensures this prints above the progress bar if it happens during execution
    # print(f"📂 Connecting to: {DB_PATH}") 
    return sqlite3.connect(DB_PATH)

def add_column_if_missing():
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Check if table exists first
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='movies'")
        if not cursor.fetchone():
            print(f"❌ CRITICAL: Table 'movies' not found in {DB_PATH}")
            print("   -> Are you sure this is the correct database file?")
            exit(1)

        # Try to select the column to see if it exists
        cursor.execute("SELECT community_rating FROM movies LIMIT 1")
    except sqlite3.OperationalError as e:
        if "no such column" in str(e):
            print("⚠️ 'community_rating' column missing. Adding it now...")
            cursor.execute("ALTER TABLE movies ADD COLUMN community_rating REAL DEFAULT 0.0")
            conn.commit()
        else:
            print(f"❌ DB Error: {e}")
            exit(1)
    finally:
        conn.close()

def fetch_tmdb_rating(title, year):
    url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": TMDB_KEY,
        "query": title,
        "year": year,
        "include_adult": "false"
    }
    
    try:
        res = requests.get(url, params=params)
        if res.status_code != 200:
            return 0.0
            
        data = res.json()
        if data.get("results"):
            # Return the vote average (e.g., 8.4)
            return data["results"][0]["vote_average"]
        return 0.0
    except Exception as e:
        # tqdm.write allows printing without breaking the progress bar
        tqdm.write(f"   ❌ API Error: {e}")
        return 0.0

def hydrate():
    add_column_if_missing()
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get all movies
    cursor.execute("SELECT tmdb_id, title, year FROM movies")
    movies = cursor.fetchall()
    
    updated_count = 0
    
    # --- TQDM LOOP ---
    # Create the progress bar object
    pbar = tqdm(movies, desc="Initializing", unit="film")
    
    for movie in pbar:
        db_id, title, year = movie
        
        # Update the bar text to show what we are currently searching
        pbar.set_description(f"🔎 {title[:30]}") 
        
        rating = fetch_tmdb_rating(title, year)
        rating = round(rating, 1)
        
        if rating > 0:
            cursor.execute(
                "UPDATE movies SET community_rating = ? WHERE tmdb_id = ?", 
                (rating, db_id)
            )
            # Use tqdm.write for logs so they don't break the bar layout
            # tqdm.write(f"✅ Found: {title} ({rating})") 
            updated_count += 1
        else:
            # tqdm.write(f"⚠️ No rating: {title}")
            pass
            
        # Sleep briefly to be nice to the API
        time.sleep(0.1)

    conn.commit()
    conn.close()
    print(f"\n🎉 DONE! Updated {updated_count} movies with real community ratings.")

if __name__ == "__main__":
    hydrate()