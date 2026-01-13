import pandas as pd
import psycopg2
from google import genai
from google.genai import types
from tqdm import tqdm
import os
import time
import json
from dotenv import load_dotenv
import logging

# --- CONFIGURATION ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ Missing GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DB Configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "motif_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "port": os.getenv("DB_PORT", 5432)
}

def create_production_schema(cur):
    """Create the production database schema with all required columns"""
    logger.info("🛠️ Creating Enhanced Production Schema...")
    
    # Create movies table with all enhancements
    cur.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id SERIAL PRIMARY KEY,
            tmdb_id INTEGER UNIQUE,
            title TEXT NOT NULL,
            overview TEXT,
            synthetic_vibe TEXT,
            tags JSONB, -- Changed from TEXT to JSONB for better querying
            poster_url TEXT,
            trailer_url TEXT,
            director TEXT,
            cast_members TEXT,
            writer TEXT,
            cinematographer TEXT,
            composer TEXT,
            producer TEXT,
            runtime INTEGER,
            rating NUMERIC(3,1),
            popularity NUMERIC(12,3),
            release_year INTEGER,
            genres TEXT,
            tagline TEXT,
            rag_content TEXT, -- Added for debugging/reference
            structured_metadata JSONB, -- New: structured metadata for filtering
            embedding vector(768),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            -- Enhanced search vector for hybrid keyword matching
            search_vector tsvector GENERATED ALWAYS AS (
                to_tsvector('english', coalesce(title, '')) || 
                to_tsvector('english', coalesce(genres, '')) || 
                to_tsvector('english', coalesce(director, '')) ||
                to_tsvector('english', coalesce(synthetic_vibe, '')) ||
                to_tsvector('english', coalesce(tags::text, ''))
            ) STORED
        );
    """)
    
    # Create update timestamp trigger
    cur.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    cur.execute("""
        DROP TRIGGER IF EXISTS update_movies_updated_at ON movies;
        CREATE TRIGGER update_movies_updated_at 
            BEFORE UPDATE ON movies 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
    """)

def validate_dataframe(df):
    """Validate and clean the dataframe before ingestion"""
    logger.info("🔍 Validating data structure...")
    
    # Check required columns
    required_columns = ['id', 'title', 'synthetic_vibe', 'rag_content']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"❌ Missing required columns: {missing_columns}")
    
    # Fill missing values
    df = df.fillna("")
    
    # Ensure proper data types for critical columns
    if 'tags' in df.columns:
        # Convert tags to proper JSON
        def convert_tags(tags):
            if pd.isna(tags):
                return json.dumps([])
            if isinstance(tags, str):
                if tags.startswith('[') and tags.endswith(']'):
                    try:
                        # Already JSON, just ensure it's valid
                        parsed = json.loads(tags)
                        return json.dumps(parsed if isinstance(parsed, list) else [])
                    except:
                        # Try comma-separated
                        tags_list = [t.strip() for t in tags.split(',') if t.strip()]
                        return json.dumps(tags_list)
                elif tags:
                    # Single tag or comma-separated
                    tags_list = [t.strip() for t in tags.split(',') if t.strip()]
                    return json.dumps(tags_list)
            elif isinstance(tags, list):
                return json.dumps(tags)
            return json.dumps([])
        
        df['tags'] = df['tags'].apply(convert_tags)
    
    # Parse structured_metadata if it exists
    if 'structured_metadata' in df.columns:
        def parse_metadata(meta):
            if pd.isna(meta):
                return json.dumps({})
            if isinstance(meta, str) and meta:
                try:
                    parsed = json.loads(meta)
                    return json.dumps(parsed if isinstance(parsed, dict) else {})
                except:
                    return json.dumps({})
            elif isinstance(meta, dict):
                return json.dumps(meta)
            return json.dumps({})
        
        df['structured_metadata'] = df['structured_metadata'].apply(parse_metadata)
    
    # Ensure numeric columns are properly typed
    numeric_columns = ['rating', 'popularity', 'release_year', 'runtime']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    logger.info(f"✅ Data validation complete. {len(df)} records ready for ingestion.")
    return df

def generate_embedding(content):
    """Generate embedding with retry logic"""
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            res = client.models.embed_content(
                model="text-embedding-004",
                contents=content,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
            )
            return res.embeddings[0].values
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Embedding attempt {attempt + 1} failed: {e}. Retrying...")
                time.sleep(retry_delay * (attempt + 1))
            else:
                logger.error(f"Embedding failed after {max_retries} attempts: {e}")
                raise
    
    raise Exception("Failed to generate embedding after retries")

def ingest_movie_batch(df, conn, batch_size=5):
    """Ingest movies in batches for better performance"""
    cur = conn.cursor()
    
    # Prepare batch data
    insert_data = []
    embedding_cache = {}  # Cache embeddings for duplicate rag_content
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Preparing data"):
        try:
            # Use rag_content for embedding
            rag_content = str(row.get('rag_content', ''))
            if not rag_content:
                rag_content = f"{row.get('title', '')} {row.get('overview', '')} {row.get('synthetic_vibe', '')}"
            
            # Cache embeddings to avoid redundant API calls
            if rag_content in embedding_cache:
                vector = embedding_cache[rag_content]
            else:
                vector = generate_embedding(rag_content)
                embedding_cache[rag_content] = vector
                time.sleep(0.01)  # Rate limiting
            
            # Prepare row data
            row_data = (
                int(row.get('id', 0)),
                str(row.get('title', '')),
                str(row.get('overview', '')),
                str(row.get('synthetic_vibe', '')),
                json.loads(row.get('tags', '[]')) if 'tags' in row else [],  # Store as JSONB
                str(row.get('poster_url', '')),
                str(row.get('trailer_url', '')),
                str(row.get('director', '')),
                str(row.get('cast', '')),
                str(row.get('writer', '')),
                str(row.get('cinematographer', '')),
                str(row.get('composer', '')),
                str(row.get('producer', '')),
                int(row.get('runtime', 0)),
                float(row.get('rating', 0.0)),
                float(row.get('popularity', 0.0)),
                int(row.get('release_year', 0)),
                str(row.get('genres', '')),
                str(row.get('tagline', '')),
                rag_content,
                json.loads(row.get('structured_metadata', '{}')) if 'structured_metadata' in row else {},  # Store as JSONB
                vector
            )
            
            insert_data.append(row_data)
            
        except Exception as e:
            logger.error(f"Error preparing row {idx} ({row.get('title', 'Unknown')}): {e}")
    
    # Batch insert
    logger.info(f"📦 Inserting {len(insert_data)} movies in batches...")
    
    insert_query = """
        INSERT INTO movies (
            tmdb_id, title, overview, synthetic_vibe, tags, poster_url, 
            trailer_url, director, cast_members, writer, cinematographer,
            composer, producer, runtime, rating, popularity, release_year,
            genres, tagline, rag_content, structured_metadata, embedding
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (tmdb_id) DO UPDATE SET
            title = EXCLUDED.title,
            overview = EXCLUDED.overview,
            synthetic_vibe = EXCLUDED.synthetic_vibe,
            tags = EXCLUDED.tags,
            poster_url = EXCLUDED.poster_url,
            trailer_url = EXCLUDED.trailer_url,
            director = EXCLUDED.director,
            cast_members = EXCLUDED.cast_members,
            writer = EXCLUDED.writer,
            cinematographer = EXCLUDED.cinematographer,
            composer = EXCLUDED.composer,
            producer = EXCLUDED.producer,
            runtime = EXCLUDED.runtime,
            rating = EXCLUDED.rating,
            popularity = EXCLUDED.popularity,
            release_year = EXCLUDED.release_year,
            genres = EXCLUDED.genres,
            tagline = EXCLUDED.tagline,
            rag_content = EXCLUDED.rag_content,
            structured_metadata = EXCLUDED.structured_metadata,
            embedding = EXCLUDED.embedding,
            updated_at = CURRENT_TIMESTAMP
    """
    
    # Insert in batches
    for i in tqdm(range(0, len(insert_data), batch_size), desc="Inserting batches"):
        batch = insert_data[i:i + batch_size]
        try:
            cur.executemany(insert_query, batch)
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error inserting batch starting at index {i}: {e}")
            # Try inserting one by one for this batch
            for j, item in enumerate(batch):
                try:
                    cur.execute(insert_query, item)
                    conn.commit()
                except Exception as single_error:
                    conn.rollback()
                    logger.error(f"Failed to insert individual item {i + j}: {single_error}")
    
    cur.close()
    logger.info(f"✅ Inserted {len(insert_data)} movies")

def create_indexes(conn):
    """Create optimal indexes for search performance"""
    logger.info("⚡ Building Optimized Indexes...")
    cur = conn.cursor()
    
    try:
        # Create HNSW index for vector similarity search (better than ivfflat for high-dim)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_movies_embedding_hnsw 
            ON movies USING hnsw (embedding vector_cosine_ops);
        """)
        
        # Create GIN index for full-text search
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_movies_search_vector 
            ON movies USING GIN (search_vector);
        """)
        
        # Create indexes for structured metadata
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_movies_tags 
            ON movies USING GIN (tags);
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_movies_metadata 
            ON movies USING GIN (structured_metadata);
        """)
        
        # Create B-tree indexes for filtering
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_movies_popularity 
            ON movies (popularity DESC);
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_movies_year 
            ON movies (release_year DESC);
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_movies_rating 
            ON movies (rating DESC);
        """)
        
        # Create composite index for common filters
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_movies_filter 
            ON movies (release_year, rating, popularity);
        """)
        
        conn.commit()
        logger.info("✅ Indexes created successfully")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating indexes: {e}")
        raise
    finally:
        cur.close()

def create_search_view(conn):
    """Create materialized view for optimized search performance"""
    logger.info("🔍 Creating Search Optimization View...")
    cur = conn.cursor()
    
    try:
        cur.execute("""
            DROP MATERIALIZED VIEW IF EXISTS movie_search_optimized;
        """)
        
        cur.execute("""
            CREATE MATERIALIZED VIEW movie_search_optimized AS
            SELECT 
                id,
                tmdb_id,
                title,
                synthetic_vibe,
                tags,
                structured_metadata,
                popularity,
                release_year,
                rating,
                embedding,
                search_vector
            FROM movies
            WHERE synthetic_vibe IS NOT NULL 
              AND synthetic_vibe != ''
              AND embedding IS NOT NULL
            WITH DATA;
        """)
        
        # Create indexes on the materialized view
        cur.execute("""
            CREATE INDEX idx_search_opt_embedding 
            ON movie_search_optimized USING hnsw (embedding vector_cosine_ops);
        """)
        
        cur.execute("""
            CREATE INDEX idx_search_opt_popularity 
            ON movie_search_optimized (popularity DESC);
        """)
        
        cur.execute("""
            CREATE INDEX idx_search_opt_search_vector 
            ON movie_search_optimized USING GIN (search_vector);
        """)
        
        conn.commit()
        logger.info("✅ Materialized view created successfully")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating materialized view: {e}")
    finally:
        cur.close()

def ingest_production():
    """Main ingestion function"""
    logger.info("🚀 Starting Production Ingestion...")
    
    # 1. Connect to database
    logger.info("🔌 Connecting to Motif DB...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False  # Use explicit transactions
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return
    
    try:
        cur = conn.cursor()
        
        # 2. Setup extensions
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        conn.commit()
        
        # 3. Create or update schema
        create_production_schema(cur)
        conn.commit()
        
        # 4. Load and validate data
        script_dir = os.path.dirname(os.path.abspath(__file__))
        input_csv = os.path.join(script_dir, "../data/motif_final_rag.csv")
        
        if not os.path.exists(input_csv):
            raise FileNotFoundError(f"❌ Error: {input_csv} not found.")
        
        logger.info(f"📂 Loading data from {input_csv}")
        df = pd.read_csv(input_csv)
        
        # Validate and clean data
        df = validate_dataframe(df)
        
        # 5. Ingest movies
        ingest_movie_batch(df, conn, batch_size=10)
        
        # 6. Create indexes
        create_indexes(conn)
        
        # 7. Create search optimization view
        create_search_view(conn)
        
        # 8. Verify ingestion
        cur.execute("SELECT COUNT(*) as total, COUNT(DISTINCT tmdb_id) as unique FROM movies;")
        counts = cur.fetchone()
        logger.info(f"📊 Database Stats: {counts['total']} total records, {counts['unique']} unique movies")
        
        cur.execute("SELECT title, tmdb_id FROM movies LIMIT 5;")
        sample = cur.fetchall()
        logger.info("📝 Sample movies:")
        for movie in sample:
            logger.info(f"  - {movie['title']} (ID: {movie['tmdb_id']})")
        
        conn.commit()
        logger.info("✅ Ingestion Complete! Database is updated and optimized.")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Ingestion failed: {e}")
        raise
    finally:
        if 'cur' in locals():
            cur.close()
        conn.close()

if __name__ == "__main__":
    ingest_production()