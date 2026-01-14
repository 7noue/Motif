import sqlite3
import requests
import json
import os
import time
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv
import enrich_logic

load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
DB_NAME = "motif_core.db"
CSV_PATH = "data/cleaned_movies.csv"

# --- DATABASE INIT ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    with open("schema.sql", "r") as f:
        conn.executescript(f.read())
    conn.close()

def movie_exists(movie_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM movies WHERE movie_id = ?", (movie_id,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists

# --- FETCHING ---
def fetch_tmdb_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&append_to_response=credits,videos"
    try:
        r = requests.get(url, timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def save_raw_to_db(data):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # Save Movie
    trailer = next((v['key'] for v in data.get('videos', {}).get('results', []) if v['site']=='YouTube' and v['type']=='Trailer'), "")
    cur.execute("""
        INSERT OR REPLACE INTO movies (movie_id, title, overview, release_date, popularity, poster_url, trailer_url, production_companies_str)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['id'], data['title'], data['overview'], data['release_date'], data['popularity'],
        f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}", 
        f"https://www.youtube.com/watch?v={trailer}" if trailer else "",
        ", ".join([c['name'] for c in data.get('production_companies', [])])
    ))
    
    # Save Cast (Top 8)
    for m in data.get('credits', {}).get('cast', [])[:8]:
        cur.execute("INSERT OR IGNORE INTO people (person_id, name) VALUES (?, ?)", (m['id'], m['name']))
        cur.execute("INSERT OR REPLACE INTO credits (movie_id, person_id, job) VALUES (?, ?, ?)", (data['id'], m['id'], "Actor"))
    
    conn.commit()
    conn.close()

def save_ai_enriched(movie_id, ai_data):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        UPDATE movies SET 
        primary_aesthetic=?, fit_quote=?, social_friction=?, 
        focus_load=?, tone_label=?, emotional_aftertaste=?, 
        perfect_occasion=?, similar_films=?
        WHERE movie_id=?
    """, (
        ai_data.get('primary_aesthetic'), ai_data.get('fit_quote'), ai_data.get('social_friction'),
        ai_data.get('focus_load'), ai_data.get('tone_label'), ai_data.get('emotional_aftertaste'),
        ai_data.get('perfect_occasion'), json.dumps(ai_data.get('similar_films', [])),
        movie_id
    ))
    conn.commit()
    conn.close()

# --- MAIN LOADER ---
if __name__ == "__main__":
    print(f"📂 Loading data from {CSV_PATH}...")
    
    if not os.path.exists(CSV_PATH):
        print(f"❌ Error: File {CSV_PATH} not found.")
        exit()

    df = pd.read_csv(CSV_PATH)
    if 'id' not in df.columns:
        print("❌ Error: CSV must have an 'id' column.")
        exit()

    init_db()
    
    all_ids = df['id'].unique().tolist()
    print(f"🎯 Found {len(all_ids)} movies in CSV.")
    
    # Process all 5000 (or however many are in the CSV)
    print("🚀 Starting Batch Ingestion with OLLAMA...")
    
    for mid in tqdm(all_ids):
        try:
            if movie_exists(mid):
                continue
                
            # 1. Fetch Raw (TMDB)
            raw = fetch_tmdb_details(mid)
            if raw:
                save_raw_to_db(raw)
                
                # 2. AI Enrichment (USING OLLAMA)
                ai_data = enrich_logic.generate_via_ollama(raw)
                
                if ai_data:
                    save_ai_enriched(mid, ai_data)
            
            # 0.1s delay to be nice to TMDB API
            time.sleep(0.1) 
            
        except Exception as e:
            print(f"⚠️ Error on ID {mid}: {e}")
            continue

    print("✅ Batch Loading Complete!")