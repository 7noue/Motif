import os
import json
import random
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
app = FastAPI(title="Motif Prototype API")

# Allow Svelte Frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenRouter Configuration
CLIENT = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
# Use a fast, free model for the prototype
MODEL_ID = "xiaomi/mimo-v2-flash:free"

# --- DATA MODELS ---
class MovieCard(BaseModel):
    id: int
    title: str
    poster_url: str
    trailer_url: str
    fit_quote: str       # Placeholder for the "Vibe" text
    match_score: int     # 0-100
    aesthetic_label: str # e.g. "NEON NOIR"

class SearchResponse(BaseModel):
    results: list[MovieCard]

# --- HELPER: MOCK ASSETS ---
def get_mock_poster(title: str):
    """Generates a placeholder image with the movie title on it"""
    clean_title = title.replace(" ", "+")
    # Using Placehold.co for instant, reliable images
    return f"https://placehold.co/500x750/1a1a1a/ffffff?text={clean_title}&font=playfair-display"

def get_mock_trailer():
    """Generic nature loop or Rick Roll for testing video components"""
    return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

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
    return {"status": "Prototype Online", "mode": "Generator + Placeholders"}

@app.get("/search", response_model=SearchResponse)
def search_movies(q: str):
    print(f"🧠 Generating titles for: '{q}'...")

    # 1. Ask AI for Titles Only (Fastest)
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
        # Fallback if AI fails (so frontend doesn't break)
        titles = ["Blade Runner 2049", "The Matrix", "Her", "Ex Machina"]

    # 2. Wrap in Mock Data
    results = []
    for idx, title in enumerate(titles):
        card = MovieCard(
            id=random.randint(1000, 9999), # Fake ID
            title=title,
            poster_url=get_mock_poster(title),
            trailer_url=get_mock_trailer(),
            fit_quote=get_mock_quote(),
            match_score=random.randint(85, 99),
            aesthetic_label="NEON NOIR" # Hardcoded for now, or randomize
        )
        results.append(card)

    return {"results": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)