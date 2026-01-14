import pandas as pd
import os
import json
import logging

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- STEP 1: LOAD MASTER DATA ---
script_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(script_dir, "motif_master_data_100.csv")

if not os.path.exists(input_file):
    print(f"❌ Error: Run enrich_data_100.py first!")
    exit()

df = pd.read_csv(input_file)
logger.info(f"✅ Loaded {len(df)} movies from master data")

# --- STEP 2: ENHANCED "BULLETPROOF" RAG BUILDER ---
def build_narrative_rag(row):
    """
    Constructs a semantic document optimized for Vector Search.
    Enhanced with proper field handling and structured negative space.
    """
    
    def clean_val(value, default="Unknown"):
        """Enhanced cleaning with better NaN handling"""
        if pd.isna(value):
            return default
        
        s = str(value).strip()
        if s.lower() in ['nan', 'none', '', '[]', '{}', 'null']:
            return default
        
        # Handle JSON strings
        if s.startswith('[') and s.endswith(']'):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return ", ".join([str(x).strip() for x in parsed if str(x).strip()])
            except:
                pass
        
        return s
    
    def extract_archetype(vibe_text):
        """Extract primary archetype from vibe text for structured search"""
        archetypes = ['Sigma', 'Coquette', 'Doomer', 'Femcel', 'Dark Academia', 
                     'Golden Retriever', 'Unhinged', 'Corecore', 'Literally Me', 
                     'Good For Her', 'Liminal', 'Girlboss', 'Manic Pixie']
        
        vibe_lower = vibe_text.lower()
        for archetype in archetypes:
            if archetype.lower() in vibe_lower:
                return archetype
        
        # Fallback to vibe-based inference
        if 'lonely' in vibe_lower or 'isolated' in vibe_lower:
            return 'Doomer'
        elif 'aesthetic' in vibe_lower or 'vibe' in vibe_lower:
            return 'Liminal'
        else:
            return 'Film'
    
    # 1. IDENTITY & ARCHETYPE (Highest search weight)
    title = str(row.get('title', 'Unknown')).upper()
    
    # Handle tags - convert from string/list properly
    raw_tags = row.get('tags', '')
    if isinstance(raw_tags, str) and raw_tags.startswith('['):
        try:
            tags_list = json.loads(raw_tags)
            tags_str = ", ".join([str(tag).strip() for tag in tags_list[:8]])  # Limit to 8 tags
        except:
            tags_str = clean_val(raw_tags)
    elif isinstance(raw_tags, list):
        tags_str = ", ".join([str(tag).strip() for tag in raw_tags[:8]])
    else:
        tags_str = clean_val(raw_tags)
    
    # Extract archetype from vibe
    vibe_text = clean_val(row.get('synthetic_vibe', ''), '')
    primary_archetype = extract_archetype(vibe_text)
    
    identity = f"[IDENTITY]: {title}. [ARCHETYPE]: {primary_archetype}. [TROPES]: {tags_str if tags_str and tags_str != 'Unknown' else 'Cinematic'}."
    
    # 2. THE SIGNAL (Vibes & Lore with structured metadata)
    overview = clean_val(row.get('overview', ''), 'Plot summary unavailable')
    
    # Enhanced vibe with structure
    if vibe_text and vibe_text != 'Unknown':
        # Add vibe as structured metadata
        signal = f"[VIBE_STRUCTURED]: {vibe_text} [PLOT]: {overview[:300]}"
    else:
        signal = f"[PLOT]: {overview[:300]}"
    
    # 3. THE ENTITIES (Talent with role clarity)
    cast = clean_val(row.get('cast', ''), 'Cast information unavailable')
    director = clean_val(row.get('director', ''), 'Director information unavailable')
    
    # Enhanced talent section with role context
    talent = f"[TALENT]: Directed by {director}. Starring {cast}."
    
    # 4. NEGATIVE SPACE (What this film is NOT - improves search precision)
    # Infer negative attributes from vibe and tags
    negative_keywords = []
    
    if 'horror' in tags_str.lower() or 'thriller' in tags_str.lower():
        negative_keywords.extend(['lighthearted', 'comedy', 'family-friendly'])
    if 'romance' in tags_str.lower() or 'drama' in tags_str.lower():
        negative_keywords.extend(['action-packed', 'violent', 'sci-fi'])
    if 'comedy' in tags_str.lower():
        negative_keywords.extend(['serious', 'dark', 'tragic'])
    
    # Add archetype-specific negatives
    if primary_archetype == 'Doomer':
        negative_keywords.extend(['uplifting', 'inspirational', 'feel-good'])
    elif primary_archetype == 'Coquette':
        negative_keywords.extend(['masculine', 'grimdark', 'cynical'])
    
    negative_space = f"[NOT]: {', '.join(set(negative_keywords[:3]))}." if negative_keywords else ""
    
    # 5. COMBINE WITH CLEAR SECTIONING
    sections = [
        identity,
        signal,
        talent
    ]
    
    if negative_space:
        sections.append(negative_space)
    
    final_chunk = "\n\n".join(sections)
    
    # Clean up whitespace while preserving structure
    return " ".join(final_chunk.split())

def build_structured_metadata(row):
    """
    Create structured metadata JSON for advanced filtering and explanation engine.
    """
    def safe_get(row, key, default=None):
        value = row.get(key)
        return value if pd.notna(value) else default
    
    metadata = {
        "id": int(row['id']),
        "title": safe_get(row, 'title', ''),
        "primary_archetype": "",
        "aesthetic_keywords": [],
        "tropes": [],
        "cultural_context": "",
        "search_boosters": []
    }
    
    # Extract archetype from vibe
    vibe = safe_get(row, 'synthetic_vibe', '')
    if vibe:
        # Simple archetype extraction
        archetypes = ['sigma', 'coquette', 'doomer', 'femcel', 'dark academia', 
                     'literally me', 'good for her', 'unhinged', 'corecore']
        for archetype in archetypes:
            if archetype in vibe.lower():
                metadata["primary_archetype"] = archetype.title()
                break
    
    # Extract tags
    tags = safe_get(row, 'tags', [])
    if isinstance(tags, str):
        if tags.startswith('['):
            try:
                tags = json.loads(tags)
            except:
                tags = [tags]
    elif not isinstance(tags, list):
        tags = []
    
    metadata["tropes"] = tags[:8]  # Limit to 8 tropes
    
    # Extract aesthetic keywords from vibe
    aesthetics = ['synthwave', 'cottagecore', 'brutalist', 'y2k', 'neo-noir', 
                 'dreamcore', 'old money', 'grunge', 'liminal', 'vaporwave']
    found_aesthetics = []
    if vibe:
        for aesthetic in aesthetics:
            if aesthetic in vibe.lower():
                found_aesthetics.append(aesthetic)
    
    metadata["aesthetic_keywords"] = found_aesthetics[:3]
    
    # Create search boosters (keywords for hybrid search)
    boosters = []
    if metadata["primary_archetype"]:
        boosters.append(metadata["primary_archetype"].lower())
    boosters.extend([t.lower().replace(' ', '-') for t in tags[:3]])
    boosters.extend(found_aesthetics)
    
    metadata["search_boosters"] = list(set(boosters))[:5]
    
    return json.dumps(metadata)

# --- STEP 3: APPLY & SAVE ---
print("📝 Constructing Enhanced RAG strings...")

# Build RAG content
df['rag_content'] = df.apply(build_narrative_rag, axis=1)

# Build structured metadata
df['structured_metadata'] = df.apply(build_structured_metadata, axis=1)

# Ensure all required columns exist
required_columns = ['id', 'title', 'synthetic_vibe', 'tags', 'rag_content', 
                   'structured_metadata', 'poster_url', 'overview', 'director', 
                   'cast', 'rating', 'release_year', 'popularity']

for col in required_columns:
    if col not in df.columns:
        df[col] = ''

# Select and reorder columns
output_columns = required_columns + [col for col in df.columns if col not in required_columns]
df = df[output_columns]

# Save the enhanced RAG data
output_file = os.path.join(script_dir, "motif_final_rag.csv")
df.to_csv(output_file, index=False)

# Also save a JSON version for easier consumption
json_output_file = os.path.join(script_dir, "motif_final_rag.json")
df.to_json(json_output_file, orient='records', indent=2)

print(f"✅ DONE! Enhanced RAG Ready CSV saved to {output_file}")
print(f"✅ JSON version saved to {json_output_file}")
print(f"✅ Total records: {len(df)}")
print(f"✅ Sample RAG content length: {len(df.iloc[0]['rag_content']) if len(df) > 0 else 0} chars")