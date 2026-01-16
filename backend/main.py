import os
import json
import logging
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Union
from dotenv import load_dotenv

# Import logic
from scripts.generator import TitleGenerationLayer, FilmEntry
from scripts.db import find_movie_metadata, get_simple_metadata

load_dotenv()

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MotifAPI")

app = FastAPI(title="Motif Engine API")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

layer = TitleGenerationLayer()

# --- MODELS ---

class MoviePalette(BaseModel):
    name: str
    colors: List[str]

# FIX 1: Defined BEFORE EnrichedFilmEntry
class SimilarFilm(BaseModel):
    title: str
    poster_url: Optional[str] = None
    year: Optional[int] = None

class EnrichedFilmEntry(BaseModel):
    tmdb_id: Optional[int] = None
    title: str
    year: int
    confidence_score: int
    community_rating: float = 0.0
    overview: Optional[str] = None
    runtime: Optional[int] = None
    director: Optional[str] = None
    cast: Optional[str] = None
    poster_url: Optional[str] = None
    trailer_url: Optional[str] = None
    certification: Optional[str] = None
    primary_aesthetic: Optional[str] = None
    fit_quote: Optional[str] = None
    tone_label: Optional[str] = None
    vibe_signature_label: Optional[str] = None
    vibe_signature_val: Optional[Union[int, float]] = None 
    palette: Optional[MoviePalette] = None
    
    # NEW FLAG: Tells frontend if this is a "real" movie or just an AI guess
    is_unverified: bool = False
    similar_films: List[SimilarFilm] = []

class SearchResponse(BaseModel):
    count: int
    results: List[EnrichedFilmEntry]

class ContextResponse(BaseModel):
    fit_quote: str
    social_context: str

# Define the expected JSON body for POST requests
class SearchRequest(BaseModel):
    query: str
    top_k: int = 9
    user_id: Optional[str] = None

# --- ENDPOINTS ---

@app.post("/search", response_model=SearchResponse)
@app.post("/api/search", response_model=SearchResponse) 
def search_movies(request: SearchRequest):
    logger.info(f"🔎 Search Request: {request.query}")
    
    ai_result = layer.fetch_titles(request.query)
    enriched_results = []

    for film in ai_result.titles:
        db_data = find_movie_metadata(film.title, film.year)
        
        entry_data = {
            "title": film.title,
            "year": film.year,
            "confidence_score": film.confidence_score,
        }

        if db_data:
            # --- REAL DATA FOUND ---
            palette_obj = None
            if db_data.get("palette_colors"):
                try:
                    colors = json.loads(db_data["palette_colors"]) if isinstance(db_data["palette_colors"], str) else []
                    palette_obj = MoviePalette(
                        name=db_data.get("palette_name", "Unknown"),
                        colors=colors
                    )
                except:
                    pass
            
            real_rating = db_data.get("community_rating")
            if not real_rating:
                real_rating = 0.0

            raw_similars = []
            if db_data.get("similar_films"):
                try:
                    raw_similars = json.loads(db_data["similar_films"])
                except:
                    raw_similars = [s.strip() for s in str(db_data["similar_films"]).split(',')]
            
            hydrated_similars = []
            for sim_title in raw_similars:
                # Use the new DB function to find the poster
                meta = get_simple_metadata(sim_title)
                if meta:
                    hydrated_similars.append(SimilarFilm(
                        title=meta["title"],
                        poster_url=meta["poster_url"],
                        year=meta["year"]
                    ))
                else:
                    # If not found in DB, send title only (frontend handles fallback)
                    hydrated_similars.append(SimilarFilm(title=sim_title))

            vibe_val = db_data.get("vibe_signature_val")
            if vibe_val is not None and isinstance(vibe_val, float) and vibe_val <= 1.0:
                vibe_val = int(vibe_val * 100)
            elif vibe_val is not None:
                vibe_val = int(vibe_val)

            entry_data.update({
                "tmdb_id": db_data["tmdb_id"],
                "overview": db_data["overview"],
                "runtime": db_data["runtime"],
                "community_rating": real_rating,
                "director": db_data["director"],
                "cast": db_data["cast"],
                "poster_url": db_data["poster_url"],
                "trailer_url": db_data["trailer_url"],
                "certification": db_data["certification"],
                "primary_aesthetic": db_data["primary_aesthetic"],
                "fit_quote": db_data["fit_quote"], 
                "tone_label": db_data["tone_label"],
                "vibe_signature_label": db_data["vibe_signature_label"],
                "vibe_signature_val": vibe_val,
                "palette": palette_obj,
                "similar_films": hydrated_similars, # FIX 2: Use the processed list
                "is_unverified": False
            })
        else:
            # --- MISSING DATA (AI SUGGESTION ONLY) ---
            entry_data.update({
                "tmdb_id": None, 
                "overview": "⚠️ AI Suggestion: This film is not yet archived in the Motif database.",
                "runtime": 0,
                "director": "Unknown",
                "community_rating": 0.0,
                "cast": "",
                "poster_url": None,
                "trailer_url": None,
                "certification": "AI", # Label for the UI badge
                "primary_aesthetic": "Unverified",
                "fit_quote": "Suggested by the neural engine.",
                "tone_label": "Concept",
                "vibe_signature_label": "Potential",
                "vibe_signature_val": 50,
                "palette": None,
                "similar_films": [],
                "is_unverified": True
            })
        
        enriched_results.append(EnrichedFilmEntry(**entry_data))

    return SearchResponse(
        count=len(enriched_results),
        results=enriched_results
    )

@app.get("/explain", response_model=ContextResponse)
def explain_movie(title: str, query: str):
    from openai import OpenAI
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    prompt = f"Explain why '{title}' fits '{query}' in 20 words (bro style)."

    try:
        resp = client.chat.completions.create(
            model="xiaomi/mimo-v2-flash:free",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.5
        )
        return json.loads(resp.choices[0].message.content)
    except:
        return ContextResponse(fit_quote="Vibes match.", social_context="Universal")

if __name__ == "__main__":
    import uvicorn
    # Reload=True is important for dev!
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)