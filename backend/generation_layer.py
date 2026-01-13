import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel
from dotenv import load_dotenv

# Import our Layer 2 logic
from gatekeeper import InputIntelligence, QueryIntent

load_dotenv()

# Force the output into this specific structure
class FilmEntry(BaseModel):
    title: str
    year: int

class TitleResponse(BaseModel):
    titles: list[FilmEntry]

class TitleGenerationLayer:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.intel = InputIntelligence()
        self.model_id = "gemini-2.5-flash-lite" 

        # We keep your exact rules but anchor them as System Instructions
        self.config = types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=TitleResponse, # This prevents JSON cut-offs
            system_instruction="""
            You are a film association engine. Map human intent/mood to relevant films with high cultural accuracy.
            RULES:
            1. Output ONLY a valid JSON object matching the provided schema.
            2. Return max 30 titles. Films only (no TV shows).
            3. No commentary or extra text.
            4. Rank by cultural association. If query is a VIBE, interpret it emotionally.
            5. Titles and years must be accurate. No duplicates.
            """
        )

    def fetch_titles(self, raw_input: str) -> TitleResponse:
        # 1. Intelligence Check (Layer 2)
        processed = self.intel.classify_intent(raw_input)
        
        if processed.intent == QueryIntent.LOW_SIGNAL:
            return self._get_fallback_titles()

        # 2. Generation (Layer 3)
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=processed.normalized_text,
                config=self.config
            )
            # Use .parsed to get the Pydantic object directly
            return response.parsed if response.parsed else self._get_fallback_titles()

        except Exception as e:
            print(f"[fetch_titles] Error: {e}")
            return self._get_fallback_titles()

    def _get_fallback_titles(self) -> TitleResponse:
        print(">> Triggering Fallback List")
        return TitleResponse(titles=[
            FilmEntry(title="Inception", year=2010),
            FilmEntry(title="The Matrix", year=1999),
            FilmEntry(title="Interstellar", year=2014)
        ])

if __name__ == "__main__":
    layer = TitleGenerationLayer()
    
    # Test
    query = "lonely neon city"
    result = layer.fetch_titles(query)
    print(f"\nResults for '{query}':")
    for t in result.titles[:5]:
        print(f" - {t.title} ({t.year})")