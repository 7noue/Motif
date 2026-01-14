import os
import json
import hashlib
import logging
from typing import Optional
from google import genai
from google.genai import types
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

# Assuming gatekeeper.py exists in your Motif/backend
from gatekeeper import InputIntelligence, QueryIntent

load_dotenv()

# Schema for structured output
class FilmEntry(BaseModel):
    title: str
    year: int

class TitleResponse(BaseModel):
    titles: list[FilmEntry]

class TitleGenerationLayer:
    def __init__(self, cache_file="query_cache.json"):
        # 1. Clients
        self.gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.deepseek_client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"), 
            base_url="https://api.deepseek.com"
        )
        
        # 2. Layer 2 Intel
        self.intel = InputIntelligence()
        
        # 3. Cache & Config
        self.cache_file = cache_file
        self.cache = self._load_cache()
        self.model_primary = "gemini-2.5-flash-lite"
        self.model_fallback = "deepseek-chat"
        
        # YOUR ORIGINAL PROMPT (Locked in)
        self.system_instructions = """
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
            - ACT I (Titles 1-5): THE DEFINITIVES. Direct hits, the exact director requested, or the "Icons" of the requested subculture.
            - ACT II (Titles 6-20): THE VIBE-MATCHES. Films that share the same cinematic DNA, psychological profiles, or aesthetic atmosphere.
            - ACT III (Titles 21-30): THE WILDCARDS. "Deep-cut" thematic cousins that offer a fresh or unexpected perspective while remaining culturally relevant to the query.

            OUTPUT DISCIPLINE:
            -Titles must be real, well-known films.
            -Years must be accurate.
            -No duplicate films.
            -No "hallucinating" films that don't exist.
            """

        self.gemini_config = types.GenerateContentConfig(
            temperature=0.3,
            response_mime_type="application/json",
            response_schema=TitleResponse,
            system_instruction=self.system_instructions
        )

    def _get_cache_key(self, text: str) -> str:
        return hashlib.md5(text.lower().strip().encode()).hexdigest()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as f:
                return json.load(f)
        return {}

    def _save_to_cache(self, key, data):
        self.cache[key] = data
        with open(self.cache_file, "w") as f:
            json.dump(self.cache, f)

    def _call_deepseek_fallback(self, prompt: str) -> Optional[TitleResponse]:
        """Secondary engine if Gemini fails or hits limits."""
        print(f"⚠️ Switching to DeepSeek Fallback for: {prompt}")
        try:
            response = self.deepseek_client.chat.completions.create(
                model=self.model_fallback,
                messages=[
                    {"role": "system", "content": self.system_instructions + "\nReturn ONLY valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                response_format={'type': 'json_object'},
                temperature=0.3
            )
            raw_content = response.choices[0].message.content
            return TitleResponse.model_validate_json(raw_content)
        except Exception as e:
            print(f"❌ DeepSeek Error: {e}")
            return None

    def fetch_titles(self, raw_input: str) -> TitleResponse:
        # 1. Layer 2 Intel & Normalization
        processed = self.intel.classify_intent(raw_input)
        if processed.intent == QueryIntent.LOW_SIGNAL:
            return self._get_hard_fallback()

        # 2. Cache Check
        cache_key = self._get_cache_key(processed.normalized_text)
        if cache_key in self.cache:
            print(f"🚀 Cache Hit: {processed.normalized_text}")
            return TitleResponse(titles=[FilmEntry(**t) for t in self.cache[cache_key]])

        # 3. Primary: Gemini
        try:
            resp = self.gemini_client.models.generate_content(
                model=self.model_primary,
                contents=processed.normalized_text,
                config=self.gemini_config
            )
            if resp.parsed:
                self._save_to_cache(cache_key, [t.model_dump() for t in resp.parsed.titles])
                return resp.parsed
        except Exception as e:
            print(f"⚡ Gemini Primary Failed: {e}")

        # 4. Secondary: DeepSeek
        ds_resp = self._call_deepseek_fallback(processed.normalized_text)
        if ds_resp:
            self._save_to_cache(cache_key, [t.model_dump() for t in ds_resp.titles])
            return ds_resp

        # 5. Ultimate Fail-safe
        return self._get_hard_fallback()

    def _get_hard_fallback(self) -> TitleResponse:
        return TitleResponse(titles=[
            {"title": "Inception", "year": 2010},
            {"title": "The Matrix", "year": 1999},
            {"title": "Blade Runner 2049", "year": 2017}
        ])

if __name__ == "__main__":
    layer = TitleGenerationLayer()
    test_query = "lonely neon lights"
    results = layer.fetch_titles(test_query)
    
    print(f"\n[Final Results for {test_query}]:")
    for film in results.titles[:5]:
        print(f"-> {film.title} ({film.year})")