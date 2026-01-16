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
from scripts.utils import parse_title_and_year  # <--- IMPORT THE NEW PARSER

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
    
    is_unverified: bool = False
    similar_films: List[SimilarFilm] = []

class SearchResponse(BaseModel):
    count: int
    results: List[EnrichedFilmEntry]

class ContextResponse(BaseModel):
    fit_quote: str
    social_context: str

class SearchRequest(BaseModel):
    query: str
    top_k: int = 9
    user_id: Optional[str] = None

# --- HELPERS ---

def hydrate_similars(similar_data_str):
    """
    Parses the 'similar_films' string (JSON or CSV), cleans titles, 
    and grabs posters from the DB.
    """
    raw_similars = []
    if similar_data_str:
        try:
            raw_similars = json.loads(similar_data_str)
        except:
            raw_similars = [s.strip() for s in str(similar_data_str).split(',')]
    
    hydrated = []
    for raw_t in raw_similars:
        # 1. PARSE "Title (Year)" -> "Title", Year
        clean_t, parsed_y = parse_title_and_year(raw_t)
        
        # 2. Check DB
        meta = get_simple_metadata(clean_t)
        
        if meta:
            hydrated.append(SimilarFilm(
                title=meta["title"], 
                poster_url=meta["poster_url"], 
                year=meta["year"]
            ))
        else:
            # If not in DB, use the parsed data so it looks clean in UI
            hydrated.append(SimilarFilm(title=clean_t, year=parsed_y))
            
    return hydrated

def format_db_entry(db_data, score=None):
    """Formats a DB row into our Pydantic model."""
    palette_obj = None
    if db_data.get("palette_colors"):
        try: 
            palette_obj = MoviePalette(
                name=db_data.get("palette_name", "Unknown"), 
                colors=json.loads(db_data["palette_colors"])
            )
        except: pass

    vibe_val = db_data.get("vibe_signature_val")
    if vibe_val is not None and isinstance(vibe_val, float) and vibe_val <= 1.0:
        vibe_val = int(vibe_val * 100)
    elif vibe_val is not None:
        vibe_val = int(vibe_val)

    return EnrichedFilmEntry(
        tmdb_id=db_data["tmdb_id"],
        title=db_data["title"],
        year=db_data["year"],
        confidence_score=score if score is not None else 100,
        community_rating=db_data.get("community_rating", 0.0),
        overview=db_data["overview"],
        runtime=db_data["runtime"],
        poster_url=db_data["poster_url"],
        trailer_url=db_data["trailer_url"],
        certification=db_data["certification"],
        primary_aesthetic=db_data["primary_aesthetic"],
        fit_quote=db_data["fit_quote"], 
        tone_label=db_data["tone_label"],
        vibe_signature_label=db_data["vibe_signature_label"],
        vibe_signature_val=vibe_val or 50,
        palette=palette_obj,
        # USE HELPER FUNCTION
        similar_films=hydrate_similars(db_data.get("similar_films")),
        director=db_data["director"],
        cast=db_data["cast"],
        is_unverified=False
    )

# --- ENDPOINTS ---

@app.post("/api/search", response_model=SearchResponse) 
def search_movies(request: SearchRequest):
    logger.info(f"🔎 Search Request: {request.query}")
    
    ai_result = layer.fetch_titles(request.query)
    enriched_results = []
    
    # --- DEDUPLICATION LOGIC ---
    seen_keys = set() 

    for film in ai_result.titles:
        # 1. Standardize the title and year
        clean_title, parsed_year = parse_title_and_year(film.title)
        search_year = parsed_year if parsed_year else film.year
        
        # 2. Create a unique signature (lowercase title + year)
        unique_key = (clean_title.strip().lower(), search_year)
        
        # 3. Check if we've seen this signature before
        if unique_key in seen_keys:
            logger.warning(f"🛑 DUPLICATE CAUGHT: Dropping '{clean_title}' ({search_year})")
            continue
        
        # 4. Mark as seen
        seen_keys.add(unique_key)
        
        # 5. Database Lookup
        db_data = find_movie_metadata(clean_title, search_year)
        
        if db_data:
            enriched_results.append(format_db_entry(db_data, film.confidence_score))
        else:
            enriched_results.append(EnrichedFilmEntry(
                tmdb_id=None, 
                title=clean_title, 
                year=search_year,
                confidence_score=film.confidence_score,
                overview="⚠️ AI Suggestion: Not in archives.",
                runtime=0, director="Unknown", cast="",
                community_rating=0.0,
                poster_url=None, trailer_url=None,
                certification="AI", primary_aesthetic="Unverified",
                fit_quote="Suggested by neural engine.",
                tone_label="Concept", vibe_signature_label="Potential", vibe_signature_val=50,
                palette=None, similar_films=[], is_unverified=True
            ))
    
    return SearchResponse(count=len(enriched_results), results=enriched_results)

@app.post("/api/get_movie", response_model=EnrichedFilmEntry)
def get_single_movie(request: dict = Body(...)):
    raw_query = request.get("query")
    
    # 1. PARSE THE CLICKED STRING
    # Ex: "Pulp Fiction (1994)" -> title="Pulp Fiction", year=1994
    query_title, query_year = parse_title_and_year(raw_query)
    
    logger.info(f"⚡ Smart Lookup: Raw='{raw_query}' -> Parsed='{query_title}' ({query_year})")

    # 2. STRICT DB LOOKUP
    db_data = find_movie_metadata(query_title, query_year) 

    if db_data:
        return format_db_entry(db_data, 100) # 100% score for direct lookups

    # 3. FALLBACK: NOT FOUND
    # The frontend will likely show a toast or handle this gracefully
    return EnrichedFilmEntry(
        title=query_title,
        year=query_year or 0,
        confidence_score=0,
        overview="Film not found in local database.",
        is_unverified=True,
        fit_quote="Archival error."
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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)