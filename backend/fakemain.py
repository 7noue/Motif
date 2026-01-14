import os
import json
import random
from typing import List, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
app = FastAPI(title="Motif Prototype API")

# --- CORS: CRITICAL FOR SVELTE ---
app.add_middleware(
    CORSMiddleware,
    # Allow specific origin (Svelte default) OR "*" for dev
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenRouter Configuration
CLIENT = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
MODEL_ID = "xiaomi/mimo-v2-flash:free"

# --- DATA MODELS ---

# 1. Request Model (Matches your Svelte POST body)
class SearchQuery(BaseModel):
    query: str
    top_k: Optional[int] = 9

# 2. Response Item Model
class MovieCard(BaseModel):
    id: int
    title: str
    poster_url: Optional[str] = None
    trailer_url: Optional[str] = None
    fit_quote: str
    match_score: int
    aesthetic_label: str

# --- HELPER: MOCK ASSETS ---
def get_mock_poster(title: str):
    clean_title = title.replace(" ", "+")
    return f"https://placehold.co/500x750/1a1a1a/ffffff?text={clean_title}&font=playfair-display"

def get_mock_quote():
    quotes = [
        "The visual equivalent of a double espresso.",
        "A neon-soaked nightmare that never lets up.",
        "Like a warm hug from a ghost.",
        "Pure, unfiltered adrenaline.",
        "A slow-burn that gets under your skin."
    ]
    return random.choice(quotes)

# --- ENDPOINTS ---

@app.get("/")
def health_check():
    return {"status": "Prototype Online", "mode": "Generator"}

# CRITICAL CHANGE: response_model is now List[MovieCard]
# This matches the return value AND what Svelte expects (result.map)
@app.post("/api/search", response_model=List[MovieCard])
def search_movies(payload: SearchQuery):
    q = payload.query
    print(f"🧠 Generating titles for: '{q}'...")

    prompt = (
        f"List 8 movie titles that match the vibe: '{q}'. "
        "Return STRICT JSON: {'titles': ['Movie A', 'Movie B']}"
    )

    try:
        resp = CLIENT.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": "You are a movie engine. JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={'type': 'json_object'}
        )
        data = json.loads(resp.choices[0].message.content)
        titles = data.get("titles", [])
    except Exception as e:
        print(f"❌ AI Error: {e}")
        titles = ["Blade Runner 2049", "The Matrix", "Her", "Ex Machina", "Dune", "Arrival"]

    # Wrap in Mock Data
    results = []
    aesthetics = ["CYBERPUNK", "NEON NOIR", "MINIMALIST", "RETRO WAVE", "GRUNGE"]
    
    for idx, title in enumerate(titles):
        card = MovieCard(
            id=random.randint(1000, 9999),
            title=title,
            poster_url=get_mock_poster(title),
            trailer_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            fit_quote=get_mock_quote(),
            match_score=random.randint(85, 99),
            aesthetic_label=random.choice(aesthetics)
        )
        results.append(card)

    # DIRECTLY RETURN THE LIST
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)