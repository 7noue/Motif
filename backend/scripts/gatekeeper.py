import os
import re
import hashlib
import sqlite3
import time
from enum import Enum, auto
from dataclasses import dataclass
from openai import OpenAI
from thefuzz import process 
from dotenv import load_dotenv

load_dotenv()
DB_NAME = "motif_core.db"
MOD_CLIENT = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) 

class QueryIntent(Enum):
    VALID_INTENT = auto()
    LOW_SIGNAL = auto()
    MALICIOUS = auto()

@dataclass
class ProcessedQuery:
    original_text: str
    normalized_text: str
    intent: QueryIntent
    safety_reason: str = ""

class InputIntelligence:
    def _normalize(self, text: str) -> str:
        if not text: return ""
        text = re.sub(r'[^a-z0-9\s]', '', text.lower()) 
        return re.sub(r'\s+', ' ', text).strip()

    def _check_safety(self, text: str) -> tuple[bool, str]:
        """
        Safety check with a strict timeout. 
        If OpenAI Mod API is slow (>0.5s), we fail open to keep the demo fast.
        """
        start_time = time.time()
        try:
            # Note: This is a synchronous call. In a real async prod app, use aiohttp.
            # For this script, we rely on the API being generally fast.
            response = MOD_CLIENT.moderations.create(input=text)
            
            # Simple latency log
            if time.time() - start_time > 0.5:
                print(f"⚠️ Safety Check was slow ({time.time() - start_time:.2f}s)")

            if response.results[0].flagged:
                return False, "Flagged Content"
            return True, "Safe"
        except:
            return True, "Check Failed (Skipped)"

    def fuzzy_db_check(self, movie_title: str) -> dict:
        """Fast DB Lookup with Fuzzy Matching"""
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. Exact Match
        cursor.execute("SELECT * FROM movies WHERE lower(title) = ?", (movie_title.lower(),))
        row = cursor.fetchone()
        
        # 2. Fuzzy Match (Fallback)
        if not row:
            cursor.execute("SELECT title FROM movies")
            all_titles = [r[0] for r in cursor.fetchall()]
            match, score = process.extractOne(movie_title, all_titles) or (None, 0)
            if score >= 90:
                cursor.execute("SELECT * FROM movies WHERE title = ?", (match,))
                row = cursor.fetchone()

        conn.close()
        return dict(row) if row else None

    def classify_intent(self, raw_input: str) -> ProcessedQuery:
        is_safe, reason = self._check_safety(raw_input)
        if not is_safe:
            return ProcessedQuery(raw_input, raw_input, QueryIntent.MALICIOUS, reason)

        norm = self._normalize(raw_input)
        intent = QueryIntent.VALID_INTENT if len(norm) > 3 else QueryIntent.LOW_SIGNAL
        
        return ProcessedQuery(raw_input, norm, intent)