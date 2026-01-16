import sqlite3
import os
import logging
from typing import Optional

# --- PATH SETUP ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
DB_PATH = os.path.join(BACKEND_DIR, "movies.db")
LOG_PATH = os.path.join(BACKEND_DIR, "db_activity.log")

# --- LOGGING ---
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a' 
)
logger = logging.getLogger("DB_Logger")

def get_db_connection():
    if not os.path.exists(DB_PATH):
        msg = f"❌ CRITICAL ERROR: Database file not found at: {DB_PATH}"
        print(msg)
        logger.critical(msg)
        raise FileNotFoundError(f"Database missing: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def find_movie_metadata(title: str, year: Optional[int] = None) -> Optional[dict]:
    """
    Strict Database Lookup.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        clean_title = str(title).strip()
        
        if year and year > 1900:
            # STRICT: Title must match AND Year must be exact (or +/- 1 for release date variance)
            query = """
                SELECT * FROM movies 
                WHERE LOWER(TRIM(title)) = LOWER(?) 
                AND year = ?
            """
            cursor.execute(query, (clean_title, year))
        else:
            # TITLE ONLY: Only if we truly don't have a year.
            query = """
                SELECT * FROM movies 
                WHERE LOWER(TRIM(title)) = LOWER(?)
            """
            cursor.execute(query, (clean_title,))

        row = cursor.fetchone()
        conn.close()

        if row:
            # msg = f"✅ HIT: '{clean_title}' ({year})"
            # print(msg) # Optional: comment out to reduce console noise
            return dict(row)
        else:
            # msg = f"⚠️ MISS: '{clean_title}' ({year})"
            # print(msg)
            return None

    except Exception as e:
        err_msg = f"❌ DB ERROR: {str(e)}"
        print(err_msg)
        logger.error(err_msg)
        return None

def get_simple_metadata(title: str) -> Optional[dict]:
    """
    Quick lookup for poster URL.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT title, year, poster_url FROM movies WHERE LOWER(TRIM(title)) = LOWER(?)"
        cursor.execute(query, (title.strip(),))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception:
        return None