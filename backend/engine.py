import os
import json
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
from scripts.gatekeeper import InputIntelligence, QueryIntent

load_dotenv()

# --- CONFIG ---
# Use a Flash model for instant associations
MODEL_ID = "xiaomi/mimo-v2-flash:free" 
CLIENT = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

class FilmEntry(BaseModel):
    title: str

class TitleResponse(BaseModel):
    titles: list[FilmEntry]

class MotifEngine:
    def __init__(self):
        self.intel = InputIntelligence()

    def search(self, user_query):
        # 1. Gatekeeper (Safety)
        processed = self.intel.classify_intent(user_query)
        if processed.intent == QueryIntent.MALICIOUS:
            return {"error": "Blocked", "reason": processed.safety_reason}

        print(f"🧠 AI Associating: '{processed.normalized_text}'...")

        # 2. Association Layer (Generate Candidates via OpenRouter)
        prompt = (
            f"List 30 films relevant to: '{processed.normalized_text}'. "
            "Return STRICT JSON: {'titles': [{'title': 'Name'}]}"
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
            parsed = TitleResponse.model_validate_json(resp.choices[0].message.content)
        except Exception as e:
            print(f"❌ AI Association Error: {e}")
            return []

        # 3. Resolution Layer (Local DB Check Only)
        # Fast Mode: We only show what we have pre-loaded with Ollama.
        print(f"⚡ Matching {len(parsed.titles)} candidates against local DB...")
        results = []
        
        for t in parsed.titles:
            # Fuzzy check matches the AI title to your SQLite rows
            match = self.intel.fuzzy_db_check(t.title)
            if match:
                results.append(dict(match))
                
        return results

if __name__ == "__main__":
    engine = MotifEngine()
    
    # Test Query
    q = "Movies like Oldboy but less gory"
    print(f"\n🔎 Searching: {q}")
    
    matches = engine.search(q)
    print(f"\n✅ Found {len(matches)} matches in DB:")
    
    for m in matches:
        print(f"🎥 {m['title']} | {m.get('primary_aesthetic', 'N/A')}")