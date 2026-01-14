-- Enhanced production schema for Motif Pro Engine
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Main movies table with ALL your data columns
CREATE TABLE movies (
    tmdb_id INTEGER PRIMARY KEY,      -- Use TMDB ID as primary key
    title TEXT NOT NULL,
    overview TEXT,
    synthetic_vibe TEXT,
    tags JSONB DEFAULT '[]',          -- Your tags from enhanced pipeline
    director TEXT,
    cast_members TEXT,
    writer TEXT,
    cinematographer TEXT,
    composer TEXT,
    producer TEXT,
    poster_url TEXT,
    trailer_url TEXT,
    runtime INTEGER,
    rating NUMERIC(3,1),
    popularity NUMERIC(12,3),
    release_year INTEGER,
    genres TEXT,
    tagline TEXT,
    rag_content TEXT,                  -- Your RAG strings
    structured_metadata JSONB DEFAULT '{}',  -- Enhanced metadata
    embedding vector(768),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Generated column for full-text search (matches your ingest.py)
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(title, '')) || 
        to_tsvector('english', coalesce(genres, '')) || 
        to_tsvector('english', coalesce(director, '')) ||
        to_tsvector('english', coalesce(synthetic_vibe, '')) ||
        to_tsvector('english', coalesce(tags::text, ''))
    ) STORED
);

-- CRITICAL INDEXES (MUST CREATE)
-- 1. Vector similarity index (choose ONE based on your scale)
CREATE INDEX idx_movies_embedding_ivfflat ON movies 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);  -- For <10K movies

-- OR for better accuracy (slower build):
-- CREATE INDEX idx_movies_embedding_hnsw ON movies 
-- USING hnsw (embedding vector_cosine_ops);

-- 2. Full-text search index (required for your API)
CREATE INDEX idx_movies_search_vector ON movies USING GIN (search_vector);

-- 3. JSONB indexes for structured queries
CREATE INDEX idx_movies_tags ON movies USING GIN (tags);
CREATE INDEX idx_movies_metadata ON movies USING GIN (structured_metadata);

-- 4. Filtering indexes
CREATE INDEX idx_movies_popularity ON movies(popularity DESC);
CREATE INDEX idx_movies_year ON movies(release_year DESC);
CREATE INDEX idx_movies_rating ON movies(rating DESC);

-- 5. Update trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_movies_updated_at 
    BEFORE UPDATE ON movies 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- OPTIONAL: Materialized view for heavy search loads
CREATE MATERIALIZED VIEW IF NOT EXISTS movie_search_cache AS
SELECT 
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

CREATE INDEX idx_search_cache_embedding ON movie_search_cache USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_search_cache_search ON movie_search_cache USING GIN (search_vector);