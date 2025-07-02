# Supabase Migration Summary

This document summarizes the changes made to migrate from Weaviate to Supabase vector storage.

## Files Modified

### 1. `backend/ingest.py`
**Changes:**
- ✅ Replaced Weaviate imports with Supabase imports
- ✅ Updated `ingest_docs()` function to use Supabase instead of Weaviate
- ✅ Replaced Weaviate client creation with Supabase client creation
- ✅ Updated vector store initialization to use `SupabaseVectorStore`
- ✅ Updated record manager namespace from `weaviate/` to `supabase/`

**Key Code Changes:**
```python
# OLD (Weaviate)
import weaviate
from langchain_weaviate import WeaviateVectorStore

with weaviate.connect_to_weaviate_cloud(...) as weaviate_client:
    vectorstore = WeaviateVectorStore(
        client=weaviate_client,
        index_name=WEAVIATE_DOCS_INDEX_NAME,
        text_key="text",
        embedding=embedding,
        attributes=["source", "title"],
    )

# NEW (Supabase)
from langchain_community.vectorstores import SupabaseVectorStore
from supabase import create_client

client = create_client(supabase_url, supabase_key)
vectorstore = SupabaseVectorStore(
    client=client,
    embedding=embedding,
    table_name="embeddings_materialized",
    query_name="match_embeddings_materialized",
)
```

### 2. `backend/retrieval.py`
**Changes:**
- ✅ Replaced Weaviate imports with Supabase imports
- ✅ Renamed `make_weaviate_retriever()` to `make_supabase_retriever()`
- ✅ Updated `make_retriever()` function to use Supabase instead of Weaviate
- ✅ Updated vector store initialization to use `SupabaseVectorStore`

**Key Code Changes:**
```python
# OLD (Weaviate)
import weaviate
from langchain_weaviate import WeaviateVectorStore

@contextmanager
def make_weaviate_retriever(...):
    with weaviate.connect_to_weaviate_cloud(...) as weaviate_client:
        store = WeaviateVectorStore(...)

# NEW (Supabase)
from langchain_community.vectorstores import SupabaseVectorStore
from supabase import create_client

@contextmanager
def make_supabase_retriever(...):
    client = create_client(supabase_url, supabase_key)
    store = SupabaseVectorStore(...)
```

### 3. `backend/configuration.py`
**Changes:**
- ✅ Updated `retriever_provider` type annotation from `Literal["weaviate"]` to `Literal["supabase"]`
- ✅ Updated default value from `"weaviate"` to `"supabase"`

### 4. `backend/constants.py`
**Changes:**
- ✅ Replaced `WEAVIATE_DOCS_INDEX_NAME` with Supabase-specific constants
- ✅ Added `SUPABASE_EMBEDDINGS_TABLE` and `SUPABASE_MATCH_FUNCTION` constants

### 5. `pyproject.toml`
**Changes:**
- ✅ Removed `langchain-weaviate` dependency
- ✅ Removed `weaviate-client` dependency
- ✅ Added `supabase = "^2.0.0"` dependency

## Environment Variables Required

The following environment variables need to be configured for Supabase:

```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Record Manager (can use Supabase PostgreSQL URL)
RECORD_MANAGER_DB_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
```

## Supabase Database Setup Required

Before running the ingestion, ensure your Supabase database has:

1. **Vector Extension Enabled:**
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. **Embeddings Table:**
   ```sql
   CREATE TABLE embeddings_materialized (
     id BIGSERIAL PRIMARY KEY,
     content TEXT,
     metadata JSONB,
     embedding VECTOR(1536)  -- Adjust dimension based on your embedding model
   );
   ```

3. **Matching Function:**
   ```sql
   CREATE OR REPLACE FUNCTION match_embeddings_materialized(
     query_embedding VECTOR(1536),
     match_threshold FLOAT DEFAULT 0.78,
     match_count INT DEFAULT 10
   )
   RETURNS TABLE(
     id BIGINT,
     content TEXT,
     metadata JSONB,
     similarity FLOAT
   )
   LANGUAGE SQL STABLE
   AS $$
     SELECT
       embeddings_materialized.id,
       embeddings_materialized.content,
       embeddings_materialized.metadata,
       1 - (embeddings_materialized.embedding <=> query_embedding) AS similarity
     FROM embeddings_materialized
     WHERE 1 - (embeddings_materialized.embedding <=> query_embedding) > match_threshold
     ORDER BY embeddings_materialized.embedding <=> query_embedding
     LIMIT match_count;
   $$;
   ```

## Migration Complete ✅

All requested changes have been implemented:
- ✅ Replaced Weaviate code in `backend/ingest.py`
- ✅ Replaced Weaviate code in `backend/retrieval.py` (equivalent to `chain.py`)
- ✅ Updated SQLRecordManager to use Supabase-compatible configuration
- ✅ Updated dependencies and configuration files

The application is now configured to use Supabase as the vector database instead of Weaviate.