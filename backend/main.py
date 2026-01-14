import os
import json
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from scripts.generator import TitleGenerationLayer, FilmEntry

load_dotenv()

# --- CONFIG ---
app = FastAPI(title="Motif Engine API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the title generation layer
layer = TitleGenerationLayer()

# --- Pydantic Models ---

class SearchResponse(BaseModel):
    count: int
    results: list[FilmEntry]

class ContextResponse(BaseModel):
    fit_quote: str
    social_context: str

# --- API ENDPOINTS ---
@app.get("/")
def health_check():
    return {"status": "Motif Engine Online", "version": "2.0"}

@app.get("/search", response_model=SearchResponse)
def search_movies(q: str = Query(..., min_length=2)):
    """
    Returns up to 30 AI-associated films with confidence scores.
    """
    result = layer.fetch_titles(q)
    results_dicts = [t.model_dump() for t in result.titles]
    return SearchResponse(
        count=len(result.titles),
        results=result.titles
    )

@app.get("/explain", response_model=ContextResponse)
def explain_movie(title: str, query: str):
    """
    Returns real-time explanation for a specific film.
    Generates a fit_quote + social_context in a human/bro tone.
    """
    from openai import OpenAI
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    prompt = f"""
User Query: "{query}"
Selected Movie: "{title}"

Task: Write a short, human/bro-style explanation (max 20 words) why this film fits the user's query.
Tone: Friendly, relatable, casual, insightful, not invasive.
Include also a short social context hint (1–2 words), like "watch with friends" or "solo chill".
Return ONLY valid JSON:
{{ "fit_quote": "string", "social_context": "string" }}
"""

    try:
        resp = client.chat.completions.create(
            model="xiaomi/mimo-v2-flash:free",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.5
        )
        return json.loads(resp.choices[0].message.content)

    except Exception as e:
        print(f"❌ OpenRouter Explain Error: {e}")
        return ContextResponse(
            fit_quote=f"This movie vibes with '{query}' perfectly.",
            social_context="Universal"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
