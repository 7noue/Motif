import os
import json
import hashlib
import logging  # <--- Added logging import
from typing import Optional
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
import json_repair

# Import our Layer 2 logic
from scripts.gatekeeper import InputIntelligence, QueryIntent
# from gatekeeper import InputIntelligence, QueryIntent

load_dotenv()

# --- LOGGING CONFIGURATION ---
# This sets up the logger to print nicely formatted messages with timestamps
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("MotifEngine")

# Force the output into this specific structure
class FilmEntry(BaseModel):
    title: str
    year: int
    confidence_score: int

class TitleResponse(BaseModel):
    titles: list[FilmEntry]

class TitleGenerationLayer:
    def __init__(self, cache_file="query_cache.json"):
        # 1. Single Client: OpenRouter
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        
        # 2. Model Selection: The "Free" Tier
        self.model_id = "xiaomi/mimo-v2-flash:free" 
        
        # 3. Layer 2 Intel & Cache
        self.intel = InputIntelligence()
        self.cache_file = cache_file
        self.cache = self._load_cache()

        # 4. LOCKED SYSTEM PROMPT (Do Not Modify)
        self.system_instructions = """
            You are a film association engine. Your job is to map human intent, mood, subcultural references, visual symbols, or partial information to relevant films with high cultural accuracy and "vibe" alignment.

            You do NOT explain. You do NOT chat. You ONLY return structured film associations.

            RULES (STRICT):
            -Output ONLY a valid JSON object matching the provided schema not including separate keys for "Act I" or "Act II.
            -The JSON must have EXACTLY ONE root key: "titles".
            -Return a maximum of 30 titles.
            -STRICTLY Do NOT include TV shows, miniseries, or web content. Films only.
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
            - ACT I (Titles 1-12): THE DEFINITIVES. Direct hits, the exact director requested, or the "Icons" of the requested subculture.
            - ACT II (Titles 13-25): THE VIBE-MATCHES. Films that share the same cinematic DNA, psychological profiles, or aesthetic atmosphere.
            - ACT III (Titles 26-30): THE WILDCARDS. "Deep-cut" thematic cousins that offer a fresh or unexpected perspective while remaining culturally relevant to the query.

            OUTPUT DISCIPLINE:
            -Titles must be real, well-known films.
            -Years must be accurate.
            -No duplicate films.
            -No "hallucinating" films that don't exist.
            -SORTING: The `titles` array MUST be strictly sorted by `confidence_score` in descending order (Highest first).
            -VARIANCE: Do NOT round confidence scores to the nearest 5. Use specific, granular integers (e.g., 93, 87, 64, 41) to imply calculation precision. Never output 100.

            *** CONFIDENCE COMPUTATION LAYER (THE TRUTH CHECK) ***
            You must logically CALCULATE the 'confidence_score' (0-100) for each film based on these 3 weighted layers. Do NOT just assign a high score because a film is in ACT I.

            LAYER A: SEMANTIC ACCURACY (Max 60 pts)
            - 60 pts = Literal match (Query: "Time Travel" -> Film: "Back to the Future").
            - 40 pts = Thematic match (Query: "Time Travel" -> Film: "Midnight in Paris" [Nostalgia as time travel]).
            - 10 pts = Tangential/Vibe only (Query: "Time Travel" -> Film: "Memento" [Memory structure]).
            - 0 pts = No semantic relation.

            LAYER B: CULTURAL AUTHORITY (Max 20 pts)
            - 20 pts = The definitive "Canon" movie for this topic.
            - 10 pts = A solid, respected entry.
            - 5 pts = A niche/divisive entry.

            LAYER C: SPECIFICITY BONUS (Max 20 pts)
            - 20 pts = Matches the specific emotional "tone" requested (e.g., "Depressing" vs "Fun").
            - 0 pts = Matches the genre but misses the specific mood.

            CRITICAL RULE (THE LIE DETECTOR): 
            If your best match only scores 50 points total (e.g., weak semantic link), OUTPUT 50. Do NOT inflate it to 95 just to fill the list. If the user query is gibberish or has NO matches, return low confidence scores (<30).
            """

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

    def fetch_titles(self, raw_input: str) -> TitleResponse:
        logger.info(f"🧠 Raw Input Received: '{raw_input}'")

        # 1. Intelligence Check
        processed = self.intel.classify_intent(raw_input)
        if processed.intent == QueryIntent.LOW_SIGNAL:
            logger.warning(f"Low signal query detected: '{raw_input}'")
            return self._get_hard_fallback()

        # 2. Cache Check (Updated with Error Handling)
        cache_key = self._get_cache_key(processed.normalized_text)
        if cache_key in self.cache:
            try:
                # Try to validate the cached data against the current model
                cached_titles = [FilmEntry(**t) for t in self.cache[cache_key]]
                logger.info(f"🚀 Cache Hit: '{processed.normalized_text}'")
                return TitleResponse(titles=cached_titles)
            except Exception as e:
                # If validation fails (e.g. missing fields), log it and regenerate
                logger.warning(f"⚠️ Cache invalid for '{processed.normalized_text}', regenerating... Error: {e}")
                # We do NOT return here; we let it fall through to step 3

        # 3. Generation
        logger.info(f"📡 Calling OpenRouter for query: '{processed.normalized_text}'...")
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": self.system_instructions},
                    {"role": "user", "content": processed.normalized_text},
                ],
                response_format={'type': 'json_object'},
                temperature=0.3
            )
            
            raw_content = response.choices[0].message.content
            
            # --- DEBUG LOGGING: RAW LLM OUTPUT ---
            # This shows exactly what the model sent back
            logger.info(f"📝 RAW LLM JSON:\n{raw_content}") 
            # -------------------------------------

            cleaned_data = json_repair.loads(raw_content)
            parsed_response = TitleResponse.model_validate(cleaned_data)
            
            self._save_to_cache(cache_key, [t.model_dump() for t in parsed_response.titles])
            
            logger.info(f"✅ Successfully generated {len(parsed_response.titles)} titles.")
            return parsed_response

        except Exception as e:
            logger.error(f"❌ OpenRouter Error: {e}", exc_info=True)
            return self._get_hard_fallback()

    def _get_hard_fallback(self) -> TitleResponse:
        logger.warning(">> Triggering Hard Fallback List")
        return TitleResponse(titles=[
            {"title": "Inception", "year": 2010, "confidence_score": 90},
            {"title": "The Matrix", "year": 1999, "confidence_score": 85},
            {"title": "Blade Runner 2049", "year": 2017, "confidence_score": 80}
        ])

if __name__ == "__main__":
    layer = TitleGenerationLayer()
    
    # Test 1
    query = "Dead poets society"
    result = layer.fetch_titles(query)
    print(f"\n[Final Results for '{query}']: {len(result.titles)} films found.")
    for t in result.titles[:15]:
        print(f" - {t.title} ({t.year}) - ({t.confidence_score}%)")

    # Test 2
    query = "Sigma grindset"
    result = layer.fetch_titles(query)
    print(f"\n[Final Results for '{query}']: {len(result.titles)} films found.")
    for t in result.titles[:15]:
        print(f" - {t.title} ({t.year}) - ({t.confidence_score}%)")