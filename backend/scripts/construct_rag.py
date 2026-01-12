import pandas as pd
import numpy as np
import os  # <--- Make sure this is imported

# --- STEP 1: LOAD MASTER DATA ---
# Get the folder where THIS script (construct_rag.py) lives
script_dir = os.path.dirname(os.path.abspath(__file__))

# Go up one level (..) to 'backend', then down into 'data'
input_file = os.path.join(script_dir, "../data/motif_master_data_100.csv")
print(f"📂 Loading master data from {input_file}...")
df = pd.read_csv(input_file)

# --- STEP 2: DEFINE YOUR RAG BUILDER ---
# You can edit this function as much as you want!
# --- STEP 2: DEFINE YOUR RAG BUILDER (PROFESSIONAL EDITION) ---
def build_narrative_rag(row):
    """
    Constructs a semantic document optimized for Vector Search.
    Prioritizes Identity > Vibe > Plot > Entities > Metadata.
    """
    
    # 🛡️ HELPER: Prevents "nan", "None", or empty brackets from entering the DB
    def clean_val(value):
        s = str(value).strip()
        if s.lower() in ['nan', 'none', '', '[]']:
            return None
        return s

    # --- 1. THE ANCHOR (High Semantic Weight) ---
    # "Inception (2010) is a Sci-Fi, Action film directed by Christopher Nolan."
    title = row['title']
    year = f"({int(row['year'])})" if clean_val(row.get('year')) else ""
    genres = clean_val(row.get('genres_str')) or "film"
    director = clean_val(row.get('director'))
    
    # Construct Identity Sentence
    if director:
        identity = f"{title} {year} is a {genres} film directed by {director}."
    else:
        identity = f"{title} {year} is a {genres} film."

    # --- 2. THE CONTEXT (Origin) ---
    # "Produced by A24 in USA. Language: English."
    origin_parts = []
    studio = clean_val(row.get('production_companies_str'))
    country = clean_val(row.get('production_countries'))
    lang = clean_val(row.get('original_language'))

    if studio: origin_parts.append(f"Produced by {studio}")
    if country: origin_parts.append(f"in {country}")
    
    # Combine Origin
    origin_str = " ".join(origin_parts) + "." if origin_parts else ""
    if lang: origin_str += f" Language: {lang}."

    # --- 3. THE SIGNAL (Vibe & Plot) ---
    # Explicit headers "Atmosphere" and "Synopsis" help the AI distinguish mood from action.
    vibe = clean_val(row.get('synthetic_vibe'))
    overview = clean_val(row.get('overview'))
    
    signal = ""
    if vibe: signal += f"Atmosphere: {vibe}. "
    if overview: signal += f"Synopsis: {overview}"

    # --- 4. THE ENTITIES (Talent) ---
    # "Starring Leonardo DiCaprio. Score by Hans Zimmer."
    people_parts = []
    cast = clean_val(row.get('cast'))
    writer = clean_val(row.get('writer'))
    composer = clean_val(row.get('composer'))

    if cast: people_parts.append(f"Starring: {cast}")
    if writer: people_parts.append(f"Written by {writer}")
    if composer: people_parts.append(f"Score by {composer}")
    
    people_str = ". ".join(people_parts) + "." if people_parts else ""

    # --- 5. THE DETAILS (Metadata & Keywords) ---
    # Kept at the end so they don't dilute the main vector signal.
    meta_parts = []
    
    # Tagline is high value, put it first in metadata
    tagline = clean_val(row.get('tagline'))
    if tagline: meta_parts.append(f"Tagline: '{tagline}'")

    # Stats
    runtime = clean_val(row.get('runtime'))
    rating = clean_val(row.get('vote_average'))
    if runtime: meta_parts.append(f"Runtime: {float(runtime):.0f} min")
    if rating: meta_parts.append(f"Rating: {float(rating):.1f}/10")

    # Keywords (Limit to first 15 to avoid token spam)
    keywords = clean_val(row.get('keywords_str'))
    if keywords:
        # distinct keywords only, limiting length
        kw_list = keywords.split(',')[:15] 
        meta_parts.append(f"Keywords: {', '.join(kw_list)}")

    meta_str = ". ".join(meta_parts) + "." if meta_parts else ""

    # --- COMBINE WITH SEMANTIC SPACING ---
    # Double spacing separates sections for better embedding parsing
    final_chunk = f"{identity} {origin_str}\n{signal}\n{people_str}\n{meta_str}"
    
    # Clean up any accidental double spaces
    return " ".join(final_chunk.split())

# --- STEP 3: APPLY & SAVE ---
print("📝 Constructing RAG strings...")
df['rag_content'] = df.apply(build_narrative_rag, axis=1)

output_file = "../data/motif_final_rag.csv"
df.to_csv(output_file, index=False)
print(f"✅ DONE! RAG Ready CSV saved to {output_file}")
print("Example RAG String:")
print(df['rag_content'].iloc[0])