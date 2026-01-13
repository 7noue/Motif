from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
import numpy as np
from typing import List, Optional
from dotenv import load_dotenv
import logging
from datetime import datetime

# --- CONFIGURATION & LOGGING ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ Missing GEMINI_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "motif_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "port": os.getenv("DB_PORT", 5432)
}

# Initialize Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

# Pydantic models
class SearchResult(BaseModel):
    id: int
    title: str
    synthetic_vibe: str
    poster_url: str
    overview: str
    director: str
    cast_members: str
    rating: float
    release_year: int
    popularity: float
    semantic_score: float
    keyword_score: float
    display_score: str
    structured_metadata: Optional[dict] = None

class ExplanationRequest(BaseModel):
    query: str
    movie_id: int
    movie_title: str
    vibe: str
    tags: List[str]
    overview: str
    semantic_score: float

class ExplanationResponse(BaseModel):
    explanation: str
    grounding: dict
    confidence: str

# FastAPI App
app = FastAPI(
    title="Motif Pro Engine v2.0",
    description="Advanced cultural film search with grounded explanations",
    version="2.0.0"
)

# Standard CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
def get_db():
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()

# Utility functions
def normalize_semantic_score(raw_score: float) -> float:
    """Normalize semantic score to 0-1 range with better curve"""
    # Sigmoid-like normalization
    if raw_score < 0.3:
        return 0.0
    elif raw_score > 0.85:
        return 1.0
    
    # Quadratic curve for mid-range
    normalized = (raw_score - 0.3) / 0.55
    return min(1.0, max(0.0, normalized ** 0.8))

def score_to_confidence(score: float) -> str:
    """Convert score to human-readable confidence"""
    if score >= 0.8:
        return "high"
    elif score >= 0.6:
        return "medium"
    elif score >= 0.4:
        return "low"
    else:
        return "very low"

def generate_query_embedding(query: str) -> List[float]:
    """Generate embedding for query with error handling"""
    try:
        res = client.models.embed_content(
            model="text-embedding-004",
            contents=query,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
        )
        return res.embeddings[0].values
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(status_code=500, detail="Embedding service unavailable")

# API Endpoints
@app.get("/")
def root():
    return {
        "service": "Motif Pro Engine",
        "version": "2.0.0",
        "status": "operational",
        "endpoints": {
            "search": "/search?q=query",
            "explain": "/explain (POST)",
            "health": "/health"
        }
    }

@app.get("/health")
def health_check(db = Depends(get_db)):
    """Health check endpoint"""
    try:
        cur = db.cursor()
        cur.execute("SELECT 1")
        db_status = "connected"
        cur.close()
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "gemini": "available" if GEMINI_API_KEY else "unavailable"
    }

@app.get("/search", response_model=List[SearchResult])
def hybrid_search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Results limit"),
    offset: int = Query(0, ge=0, description="Results offset"),
    min_score: float = Query(0.25, ge=0.0, le=1.0, description="Minimum semantic score threshold"),
    boost_popularity: bool = Query(False, description="Boost popular results"),
    db = Depends(get_db)
):
    """
    Advanced Hybrid Search: Combines Semantic (Vector) + Lexical (Keyword) + Structured Metadata.
    """
    logger.info(f"Search request: query='{q}', limit={limit}, offset={offset}")
    
    # 1. Generate Query Embedding
    try:
        query_vector = generate_query_embedding(q)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding error: {str(e)}")
    
    # 2. HYBRID QUERY with improved ranking
    try:
        cur = db.cursor()
        
        # Parse structured metadata for additional search boost
        # This extracts archetypes and aesthetics from metadata
        sql = """
        SELECT 
            id, title, synthetic_vibe, poster_url, overview, director,
            cast_members, rating, release_year, popularity, rag_content,
            structured_metadata,
            -- Semantic Score (Cosine Similarity)
            (1 - (embedding <=> %s::vector)) as semantic_score_raw,
            -- Lexical Score (Full-Text Search on title/vibe/tags)
            ts_rank_cd(
                to_tsvector('english', 
                    title || ' ' || 
                    COALESCE(synthetic_vibe, '') || ' ' ||
                    COALESCE(rag_content, '')
                ), 
                websearch_to_tsquery('english', %s)
            ) as keyword_score_raw
        FROM movies
        WHERE (1 - (embedding <=> %s::vector)) > %s
        """
        
        params = [query_vector, q, query_vector, min_score]
        
        # Execute query
        cur.execute(sql, params)
        raw_results = cur.fetchall()
        
        if not raw_results:
            return []
        
        # 3. ENHANCED RANKING LOGIC
        enhanced_results = []
        for r in raw_results:
            # Normalize scores
            semantic_norm = normalize_semantic_score(float(r['semantic_score_raw']))
            keyword_norm = min(1.0, float(r['keyword_score_raw']) * 2)  # Boost keyword score
            
            # Parse structured metadata for additional signals
            metadata_boost = 0.0
            metadata = {}
            if r['structured_metadata']:
                try:
                    metadata = json.loads(r['structured_metadata'])
                    # Check if query matches archetype or aesthetics
                    query_lower = q.lower()
                    if 'primary_archetype' in metadata:
                        if metadata['primary_archetype'].lower() in query_lower:
                            metadata_boost += 0.15
                    if 'search_boosters' in metadata:
                        for booster in metadata['search_boosters']:
                            if booster.lower() in query_lower:
                                metadata_boost += 0.05
                except:
                    metadata = {}
            
            # Popularity adjustment (less aggressive)
            popularity_adj = 0.0
            if boost_popularity:
                popularity_adj = np.log1p(float(r['popularity'])) * 0.05
            
            # Calculate final score with balanced weights
            final_score = (
                semantic_norm * 0.55 +      # 55% semantic similarity
                keyword_norm * 0.30 +       # 30% keyword matching
                metadata_boost +            # Up to 20% metadata matching
                popularity_adj              # 0-5% popularity boost (optional)
            )
            
            # Cap at 0.99
            final_score = min(0.99, final_score)
            
            # Prepare result
            result = dict(r)
            result['semantic_score'] = float(r['semantic_score_raw'])
            result['keyword_score'] = float(r['keyword_score_raw'])
            result['display_score'] = f"{final_score:.0%}"
            result['structured_metadata'] = metadata
            
            # Add to list with final score for sorting
            enhanced_results.append((final_score, result))
        
        # Sort by final score
        enhanced_results.sort(key=lambda x: x[0], reverse=True)
        
        # Apply limit and offset
        paginated_results = enhanced_results[offset:offset + limit]
        
        # Convert to response format
        final_results = []
        for score, result in paginated_results:
            response_item = SearchResult(
                id=result['id'],
                title=result['title'],
                synthetic_vibe=result['synthetic_vibe'] or "",
                poster_url=result['poster_url'] or "",
                overview=result['overview'] or "",
                director=result['director'] or "",
                cast_members=result['cast_members'] or "",
                rating=float(result['rating']) if result['rating'] else 0.0,
                release_year=int(result['release_year']) if result['release_year'] else 0,
                popularity=float(result['popularity']) if result['popularity'] else 0.0,
                semantic_score=result['semantic_score'],
                keyword_score=result['keyword_score'],
                display_score=result['display_score'],
                structured_metadata=result['structured_metadata']
            )
            final_results.append(response_item)
        
        logger.info(f"Search completed: {len(final_results)} results")
        return final_results
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal search failure: {str(e)}")
    finally:
        if 'cur' in locals():
            cur.close()

@app.post("/explain", response_model=ExplanationResponse)
def explain_recommendation(request: ExplanationRequest):
    """
    Enhanced explanation agent with grounded reasoning.
    Uses structured metadata and specific evidence from the film.
    """
    logger.info(f"Explanation request for movie {request.movie_id}: {request.movie_title}")
    
    # Parse tags if they're in string format
    if isinstance(request.tags, str):
        try:
            tags_list = json.loads(request.tags)
        except:
            tags_list = [tag.strip() for tag in request.tags.split(',')]
    else:
        tags_list = request.tags
    
    # Limit tags for clarity
    top_tags = tags_list[:3]
    
    # Determine confidence from semantic score
    confidence = score_to_confidence(request.semantic_score)
    
    # Create grounded evidence
    grounding_evidence = {
        "top_tropes": top_tags,
        "semantic_match": f"{request.semantic_score:.1%}",
        "confidence_level": confidence,
        "query_terms": request.query.lower().split()[:5]
    }
    
    # Enhanced prompt with grounding
    prompt = f"""
## ROLE: CULTURAL MATCH EXPLAINER
You explain why specific films match user queries using internet culture vocabulary.

## GROUNDING EVIDENCE
- User Query: "{request.query}"
- Film: "{request.movie_title}"
- Primary Vibe: "{request.vibe[:200] if request.vibe else 'No vibe available'}"
- Key Tropes: {', '.join(top_tags)}
- Plot Snapshot: "{request.overview[:150] if request.overview else 'No plot summary'}"

## MATCH CONTEXT
Semantic Match Strength: {request.semantic_score:.1%} ({confidence} confidence)

## TASK
Explain the connection between the query and the film. Use this structure:
1. **Cultural Bridge**: How the film's vibe/tropes connect to the query's intent
2. **Specific Evidence**: Reference specific tropes or vibe elements that match
3. **Use Case**: When/why someone searching for this would watch it

## GUIDELINES
- BE SPECIFIC: Reference actual tropes and vibe elements
- BE CONCISE: 2-3 sentences maximum
- BE GROUNDED: Use evidence from the grounding data
- TONE: Knowledgeable, slightly online, helpful

## EXAMPLES
Query: "sigma male loner film"
Vibe: "Doomer capitalist critique with liminal office spaces"
Tropes: ["Anti-Hero", "Corporate Dystopia", "Existential Crisis"]
Response: "This is peak Sigma cinema. The liminal office spaces and anti-hero's existential crisis capture the modern masculine isolation. Perfect for late-night capitalist dread viewing."

## YOUR EXPLANATION (2-3 sentences):
"""
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",  # Using experimental model for better reasoning
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                top_p=0.8,
                max_output_tokens=150
            )
        )
        
        explanation = response.text.strip()
        
        # Clean up the response
        if explanation.startswith('"') and explanation.endswith('"'):
            explanation = explanation[1:-1]
        
        return ExplanationResponse(
            explanation=explanation,
            grounding=grounding_evidence,
            confidence=confidence
        )
        
    except Exception as e:
        logger.error(f"Explanation generation failed: {str(e)}")
        # Fallback explanation
        fallback = f"This film matches your query '{request.query}' through its {confidence} semantic similarity. Key elements: {', '.join(top_tags[:2])}."
        
        return ExplanationResponse(
            explanation=fallback,
            grounding=grounding_evidence,
            confidence=confidence
        )

@app.get("/movie/{movie_id}")
def get_movie_details(movie_id: int, db = Depends(get_db)):
    """Get detailed information for a specific movie"""
    try:
        cur = db.cursor()
        cur.execute("""
            SELECT id, title, synthetic_vibe, tags, overview, director,
                   cast_members, rating, release_year, popularity, poster_url,
                   trailer_url, writer, cinematographer, composer, producer,
                   rag_content, structured_metadata
            FROM movies 
            WHERE id = %s
        """, (movie_id,))
        
        result = cur.fetchone()
        cur.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="Movie not found")
        
        # Parse structured metadata
        metadata = {}
        if result['structured_metadata']:
            try:
                metadata = json.loads(result['structured_metadata'])
            except:
                metadata = {}
        
        return {
            **dict(result),
            "structured_metadata": metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Movie details error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)