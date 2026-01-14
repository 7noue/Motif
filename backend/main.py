import os
import json
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from scripts.gatekeeper import InputIntelligence, QueryIntent

load_dotenv()

# --- CONFIG ---
app = FastAPI(title="Motif Engine API")

# Enable CORS for Frontend (React/Next.js)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_ID = "xiaomi/mimo-v2-flash:free"
CLIENT = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# --- Pydantic Models ---
class FilmMatch(BaseModel):
    title: str
    confidence_score: int

class SearchResponse(BaseModel):
    matches: list[FilmMatch]

class ContextResponse(BaseModel):
    fit_quote: str
    social_context: str

# --- ENGINE LOGIC ---
class MotifEngine:
    def __init__(self):
        self.intel = InputIntelligence()

    def search_candidates(self, user_query: str):
        # 1. Gatekeeper Check
        processed = self.intel.classify_intent(user_query)
        if processed.intent == QueryIntent.MALICIOUS:
            raise HTTPException(status_code=400, detail=f"Blocked: {processed.safety_reason}")

        print(f"🧠 Scoring candidates for: '{processed.normalized_text}'...")

        # 2. AI Association (Get 30 Candidates + Scores)
        prompt = (
            f"Recommend 30 films for query: '{processed.normalized_text}'. "
            "Assign a 'confidence_score' (0-100) based on how well it fits. "
            "Return JSON: {'matches': [{'title': 'Name', 'confidence_score': 95}]}"
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
            parsed = SearchResponse.model_validate_json(resp.choices[0].message.content)
        except Exception as e:
            print(f"❌ AI Error: {e}")
            return []

        # 3. Merge with Local DB
        results = []
        for m in parsed.matches:
            db_data = self.intel.fuzzy_db_check(m.title)
            if db_data:
                # Merge DB assets with Real-Time Score
                merged = dict(db_data)
                merged['match_confidence'] = m.confidence_score
                results.append(merged)

        # Sort by Confidence
        results.sort(key=lambda x: x['match_confidence'], reverse=True)
        return results

    def generate_context(self, title: str, query: str):
        print(f"✨ Generating Live Context for '{title}'...")
        prompt = f"""
        User Query: "{query}"
        Selected Movie: "{title}"
        
        Task: Write a "Fit Quote" (Max 15 words) explaining why this movie fits THIS SPECIFIC query.
        Example: "A visual panic attack that matches your high-stress request perfectly."
        
        Return JSON: {{ "fit_quote": "string", "social_context": "string" }}
        """
        try:
            resp = CLIENT.chat.completions.create(
                model=MODEL_ID,
                messages=[{"role": "user", "content": prompt}],
                response_format={'type': 'json_object'}
            )
            return json.loads(resp.choices[0].message.content)
        except:
            return {"fit_quote": "A perfect match for your vibe.", "social_context": "Universal"}

# Initialize Engine
engine = MotifEngine()

# --- API ENDPOINTS ---

@app.get("/")
def health_check():
    return {"status": "Motif Engine Online", "version": "2.0"}

@app.get("/search")
def search_movies(q: str = Query(..., min_length=2)):
    """
    Returns a list of movies from local DB that match the AI's associations.
    """
    results = engine.search_candidates(q)
    return {"count": len(results), "results": results}

@app.get("/explain")
def explain_movie(title: str, query: str):
    """
    Returns the real-time 'Fit Quote' and Context.
    Trigger this when the user clicks a card.
    """
    context = engine.generate_context(title, query)
    return context

if __name__ == "__main__":
    import uvicorn
    # Run directly for debugging
    uvicorn.run(app, host="0.0.0.0", port=8000)