import os
import json
import ollama
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# OpenRouter Client (For Live Engine / Fast Mode)
OR_CLIENT = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
# Use a fast/cheap model for live tasks
OR_MODEL = "google/gemini-2.0-flash-exp:free"

def _get_prompt(movie):
    return f"""
    ### SYSTEM ROLE: CULTURAL CURATOR
    Analyze film: "{movie['title']}" ({str(movie.get('release_date', ''))[:4]}).
    Synopsis: {movie['overview']}

    ### TASK: Generate strict JSON metadata.
    1. AESTHETIC LABEL (Max 2 words): Visual micro-genre (e.g., "Neon Noir").
    2. THE FIT: Punchy metaphor (Max 15 words).
    3. SOCIAL FRICTION: "Universal", "Parents Warning", "Partner Hazard", "Bro Code", "Solo Watch".
    4. FOCUS LOAD: "Locked In", "Casual", "Background".
    5. TONE: Emotion + Emoji (e.g., "Anxiety 😨").
    6. EMOTIONAL AFTERTASTE: No spoilers (e.g., "Hollow").
    7. PERFECT OCCASION: (e.g., "Rainy Sunday").
    8. SIMILAR FILMS: List 3 specific titles.

    ### OUTPUT JSON:
    {{
        "primary_aesthetic": "string",
        "fit_quote": "string",
        "social_friction": "string",
        "focus_load": "string",
        "tone_label": "string",
        "emotional_aftertaste": "string",
        "perfect_occasion": "string",
        "similar_films": ["A", "B"]
    }}
    """

def generate_via_ollama(movie):
    """Method 1: Local GPU (Free) - Used by Batch Loader"""
    try:
        response = ollama.chat(
            model="llama3.1", 
            messages=[{'role': 'user', 'content': _get_prompt(movie)}], 
            format='json'
        )
        return json.loads(response['message']['content'])
    except Exception as e:
        print(f"⚠️ Ollama Fail on {movie['title']}: {e}")
        return None

def generate_via_openrouter(movie):
    """Method 2: Cloud API (Fast) - Used by Live Engine (if needed)"""
    try:
        response = OR_CLIENT.chat.completions.create(
            model=OR_MODEL,
            messages=[
                {"role": "system", "content": "Return only valid JSON."},
                {"role": "user", "content": _get_prompt(movie)}
            ],
            response_format={'type': 'json_object'}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"⚠️ OpenRouter Fail on {movie['title']}: {e}")
        return None