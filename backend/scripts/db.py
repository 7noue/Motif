import sqlite3
import os
import logging
from typing import Optional

# --- 1. ABSOLUTE PATH SETUP ---
# Get the directory where THIS file (db.py) is located: .../Motif/backend/scripts
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up one level to the 'backend' folder
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
# Force the DB to be exactly here
DB_PATH = os.path.join(BACKEND_DIR, "movies.db")
# Log file location
LOG_PATH = os.path.join(BACKEND_DIR, "db_activity.log")

# --- 2. LOGGING CONFIGURATION ---
# This creates a file 'db_activity.log' that records every hit/miss
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a' # Append mode (doesn't overwrite old logs)
)
logger = logging.getLogger("DB_Logger")

def get_db_connection():
    if not os.path.exists(DB_PATH):
        msg = f"❌ CRITICAL ERROR: Database file not found at: {DB_PATH}"
        print(msg)
        logger.critical(msg)
        print("   -> Run 'python scripts/init_db.py' to create it.")
        raise FileNotFoundError(f"Database missing: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def find_movie_metadata(title: str, year: int) -> Optional[dict]:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        clean_title = str(title).strip()
        
        # IMPROVEMENT: Fuzzy Year Matching (Year +/- 1)
        # This catches "Fight Club 1998" vs "1999" errors from the AI
        query = """
            SELECT * FROM movies 
            WHERE LOWER(TRIM(title)) = LOWER(?) 
            AND year >= ? AND year <= ?
        """
        
        # Search for year - 1 to year + 1
        cursor.execute(query, (clean_title, year - 1, year + 1))
        row = cursor.fetchone()
        conn.close()

        if row:
            msg = f"✅ HIT: '{clean_title}' ({year})"
            print(msg)
            logger.info(msg)
            return dict(row)
        else:
            # It's okay! We will handle this gracefully in main.py
            msg = f"⚠️ MISS: '{clean_title}' ({year}) - Not in local DB"
            print(msg)
            logger.warning(msg) 
            return None

    except Exception as e:
        err_msg = f"❌ ERROR searching for '{title}': {str(e)}"
        print(err_msg)
        logger.error(err_msg)
        return None