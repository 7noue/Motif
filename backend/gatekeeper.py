import re
import hashlib
from enum import Enum, auto
from dataclasses import dataclass

# 1. Define Output Enums
class QueryIntent(Enum):
    VALID_INTENT = auto()          # Clear enough to process
    VAGUE_BUT_SALVAGEABLE = auto() # Needs Gemini Flash to interpret
    LOW_SIGNAL = auto()            # Too short or gibberish -> Fallback
    REPEAT_QUERY = auto()          # We have seen this exact hash recently

@dataclass
class ProcessedQuery:
    original_text: str
    normalized_text: str
    query_hash: str
    intent: QueryIntent

class InputIntelligence:
    def __init__(self):
        # A simple in-memory cache for demonstration. 
        # In production, this would be Redis or Memcached.
        self._query_cache = set()

    def _normalize(self, text: str) -> str:
        """
        Rules:
        1. Lowercase
        2. Strip punctuation/symbols
        3. Collapse whitespace
        4. Basic stemming (optional, simplified here)
        """
        if not text:
            return ""
        
        # Lowercase
        text = text.lower()
        
        # Remove anything that isn't alphanumeric or space
        text = re.sub(r'[^a-z0-9\s]', '', text)
        
        # Collapse multiple spaces into one and trim edges
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def _generate_hash(self, normalized_text: str) -> str:
        """Create a consistent hash for repeat detection."""
        return hashlib.md5(normalized_text.encode('utf-8')).hexdigest()

    def classify_intent(self, raw_input: str) -> ProcessedQuery:
        normalized = self._normalize(raw_input)
        q_hash = self._generate_hash(normalized)
        
        intent = QueryIntent.LOW_SIGNAL

        # Logic Gate 1: Check Cache (Repeat Detection)
        if q_hash in self._query_cache:
            intent = QueryIntent.REPEAT_QUERY
        
        # Logic Gate 2: Low Signal Heuristics
        elif len(normalized) < 2: 
            # Example: "a", " ", "."
            intent = QueryIntent.LOW_SIGNAL
            
        # Logic Gate 3: Valid vs Vague
        # If it has specific keywords (year, "movie", "film") or reasonable length
        elif len(normalized) > 3:
             # Heuristic: If it looks like a year or has specific keywords, it's valid
             # This regex looks for 4 digits (year) OR common keywords
            if re.search(r'\b(19|20)\d{2}\b', normalized) or len(normalized.split()) > 1:
                intent = QueryIntent.VALID_INTENT
                self._query_cache.add(q_hash) # Cache it now
            else:
                # One word, no year -> Might need Flash to expand
                intent = QueryIntent.VAGUE_BUT_SALVAGEABLE
                self._query_cache.add(q_hash)

        return ProcessedQuery(
            original_text=raw_input,
            normalized_text=normalized,
            query_hash=q_hash,
            intent=intent
        )

# --- Implementation Example ---

processor = InputIntelligence()

# Test cases based on your examples
inputs = [
    "Joker Movie",       # Standard
    "joker 2019",        # Specific
    "   joker    joaquin!!! ", # Dirty
    "Joker Movie",       # Repeat
    "a",                 # Low signal
    "scifi",             # Vague
]

print(f"{'RAW INPUT':<20} | {'NORMALIZED':<20} | {'INTENT'}")
print("-" * 65)

for i in inputs:
    result = processor.classify_intent(i)
    print(f"{result.original_text:<20} | {result.normalized_text:<20} | {result.intent.name}")