import pandas as pd
import numpy as np

# --- STEP 1: LOAD MASTER DATA ---
input_file = "motif_master_data_100.csv"
print(f"📂 Loading master data from {input_file}...")
df = pd.read_csv(input_file)

# --- STEP 2: DEFINE YOUR RAG BUILDER ---
# You can edit this function as much as you want!
def build_narrative_rag(row):
    """
    Constructs the final text chunk for the vector database.
    """
    # 1. Identity
    identity = f"{row['title']} ({row['year']}) is a {row['genres_str']} film directed by {row['director']}."
    
    # 2. Origin (Studio, Country, Language)
    origin = ""
    studio = str(row.get('production_companies_str', ''))
    if studio and studio.lower() != 'nan':
        origin += f" Produced by {studio}."
    
    country = str(row.get('production_countries', ''))
    if country and country.lower() != 'nan' and country != '[]':
         origin += f" Country: {country}."

    lang = str(row.get('original_language', ''))
    if lang and lang.lower() != 'nan':
         origin += f" Language: {lang}."

    # 3. Vibe & Plot
    # Check if synthetic_vibe exists, otherwise fallback
    vibe_text = str(row.get('synthetic_vibe', ''))
    content = f"Vibe: {vibe_text}. Plot: {row['overview']}"
    
    # 4. People
    people = f"Starring {row['cast']}."
    if str(row.get('writer')) != 'nan': people += f" Written by {row['writer']}."
    if str(row.get('composer')) != 'nan': people += f" Score by {row['composer']}."
        
    # 5. Technical Context
    runtime = row.get('runtime', 0)
    rating = row.get('vote_average', 0)
    context = f"Runtime: {runtime} mins. Rating: {rating}/10."
    
    if str(row.get('tagline')) != 'nan':
        context += f" Tagline: '{row['tagline']}'."

    # 6. Keywords
    keywords = f"Keywords: {row['keywords_str']}."
    
    # Combine
    return f"{identity} {origin} {content} {people} {context} {keywords}"

# --- STEP 3: APPLY & SAVE ---
print("📝 Constructing RAG strings...")
df['rag_content'] = df.apply(build_narrative_rag, axis=1)

output_file = "motif_final_rag.csv"
df.to_csv(output_file, index=False)
print(f"✅ DONE! RAG Ready CSV saved to {output_file}")
print("Example RAG String:")
print(df['rag_content'].iloc[0])