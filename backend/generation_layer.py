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
            temperature=0.3,
            response_mime_type="application/json",
            response_schema=TitleResponse, # This prevents JSON cut-offs
            system_instruction="""
             You are a film association engine. Your job is to map human intent, mood, subcultural references, visual symbols, or partial information to relevant films with high cultural accuracy and "vibe" alignment.

            You do NOT explain. You do NOT chat. You ONLY return structured film associations.

            RULES (STRICT):
            -Output ONLY a valid JSON object matching the provided schema.
            -Return a maximum of 30 titles.
            -Do NOT include TV shows, miniseries, or web content. Films only.
            -Do NOT include commentary, markdown, or extra text.
            -Optimize for Archetypal Resonance: Prioritize how a film "feels" and the "type of character" it features over literal plot summaries.

            QUERY INTERPRETATION & SUBCULTURE RULES:
            -Directorial & Visual DNA: If a query references a PERSON (e.g., "Christopher Nolan") or iconic visual symbols (e.g., "Katana Yellow Jacket"), resolve to the direct source first, then to films sharing that specific intellectual or aesthetic "DNA."
            -Social Context (Contrast Awareness): Distinguish between "Watch with friends" (prioritize high-energy, comedic, or "fun" horror like Scream) and "Watch with a partner" (prioritize intimacy, romantic tension, or emotional stakes like Past Lives).
            -Temporal Relevance (Trend Sensitivity): For current-year queries (e.g., "Best of 2025/2026"), prioritize high-velocity and acclaimed releases from the local timeline (e.g., Ryan Coogler's Sinners, Bong Joon-ho's Mickey 17, or 28 Years Later).
            -Discovery Balance (Deep-Cut Rule): Maintain a ratio of roughly 70% "Canon" (highly recognizable/popular) and 30% "Cult/Deep Cuts" (thematic cousins that are critically acclaimed but less mainstream) to provide surprise value.
            -Archetype > Industry: For subculture queries (e.g., "Sigma", "Doomer"), prioritize protagonists with specific psychological traits (stoicism, isolation, obsession) over generic industry settings.
            Avoid Keyword Traps: Do not match words literally. Do not return every movie with "rain" in the title for a "rainy day" query; return films that feel like a rainy day.
            -Subcultural Literacy: Recognize modern internet aesthetics (Corecore, Synthwave, Dark Academia). Resolve these to the "canon" films of those online communities.
            
            RANKING GUIDELINES (THE 3-ACT STRUCTURE):
            Rank the 30-film output according to this specific flow to ensure discovery:
            - ACT I (Titles 1-5): THE DEFINITIVES. Direct hits, the exact director requested, or the "Icons" of the requested subculture.
            - ACT II (Titles 6-20): THE VIBE-MATCHES. Films that share the same cinematic DNA, psychological profiles, or aesthetic atmosphere.
            - ACT III (Titles 21-30): THE WILDCARDS. "Deep-cut" thematic cousins that offer a fresh or unexpected perspective while remaining culturally relevant to the query.

            OUTPUT DISCIPLINE:
            -Titles must be real, well-known films.
            -Years must be accurate.
            -No duplicate films.
            -No "hallucinating" films that don't exist.
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
    query = "Sigma grindset"
    result = layer.fetch_titles(query)
    print(f"\nResults for '{query}':")
    for t in result.titles[:10]:
        print(f" - {t.title} ({t.year})"),

    query = "neon city loneliness"
    result = layer.fetch_titles(query)
    print(f"\nResults for '{query}':")
    for t in result.titles[:10]:
        print(f" - {t.title} ({t.year})")

    query = "wong kar wai"
    result = layer.fetch_titles(query)
    print(f"\nResults for '{query}':")
    for t in result.titles[:10]:
        print(f" - {t.title} ({t.year})")