# Web Search Migration Guide

This document outlines the migration from LangChain-specific document retrieval to a general-purpose web search system using Tavily.

## 🔄 Changes Made

### 1. Removed LangChain Document Ingestion

**Files Modified:**
- `backend/ingest.py`

**Changes:**
- Removed `load_langchain_docs()`, `load_langsmith_docs()`, `load_api_docs()`, and `load_langgraph_docs()` functions
- Replaced with `load_custom_docs()` placeholder function
- Updated `ingest_docs()` to use custom document sources instead of LangChain docs

### 2. Added Web Search Functionality

**New Files:**
- `backend/web_search.py` - Tavily web search integration

**Features:**
- Real-time web search using Tavily API
- Configurable search parameters (depth, results count, content types)
- Returns results as LangChain Document objects
- Includes AI-generated answers and web search results

### 3. Enhanced Retrieval System

**Files Modified:**
- `backend/retrieval_graph/researcher_graph/graph.py`

**Changes:**
- Updated `retrieve_documents()` to use both vector search and web search
- Added fallback mechanism: tries vector search first, then web search
- Combines results from both sources for comprehensive answers

### 4. Updated Prompts and Routing

**Files Modified:**
- `backend/retrieval_graph/prompts.py`
- `backend/retrieval_graph/graph.py`

**Changes:**
- Replaced LangSmith-pulled prompts with custom, general-purpose prompts
- Updated router to use "research" instead of "langchain" classification
- Added full routing graph with analyze → route → respond flow
- Removed LangChain-specific references from docstrings and prompts

### 5. Updated Dependencies

**Files Modified:**
- `pyproject.toml`

**Changes:**
- Added `tavily-python = "^0.3.0"`
- Kept existing Supabase and other dependencies

## 🔧 Environment Setup

### Required Environment Variables

```bash
# Tavily API Key (required for web search)
TAVILY_API_KEY=your_tavily_api_key_here

# Supabase Configuration (existing)
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Record Manager (existing)
RECORD_MANAGER_DB_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
```

### Getting a Tavily API Key

1. Visit [Tavily.com](https://tavily.com)
2. Sign up for an account
3. Navigate to your dashboard
4. Generate an API key
5. Add it to your environment variables

## 🚀 How It Works

### 1. Query Routing

The system now uses intelligent routing:

- **Research queries** → Create research plan → Conduct research → Respond
- **General queries** → Direct response (no research needed)
- **Unclear queries** → Ask for clarification

### 2. Hybrid Search

For research queries, the system performs:

1. **Vector Search** (if documents are ingested)
   - Searches your Supabase vector database
   - Returns relevant documents from ingested content

2. **Web Search** (always performed)
   - Uses Tavily to search the web in real-time
   - Gets current, authoritative information
   - Includes AI-generated answers

3. **Combined Results**
   - Merges vector and web search results
   - Provides comprehensive context for response generation

### 3. Custom Document Sources

To add your own documents instead of LangChain docs:

```python
# In backend/ingest.py, modify load_custom_docs():

def load_custom_docs():
    """Load custom documentation sources."""
    docs = []
    
    # Example: Load from your website
    docs.extend(SitemapLoader(
        "https://yoursite.com/sitemap.xml",
        filter_urls=["https://yoursite.com/docs/"],
        parsing_function=simple_extractor,
    ).load())
    
    # Example: Load from local files
    docs.extend(DirectoryLoader(
        "path/to/your/docs",
        glob="**/*.md",
        loader_cls=TextLoader,
    ).load())
    
    return docs
```

## 📊 Benefits

### 1. Real-time Information
- Web search provides current, up-to-date information
- No need to constantly re-ingest documentation

### 2. Broader Knowledge Base
- Not limited to pre-ingested documents
- Can answer questions about any topic

### 3. Intelligent Routing
- Efficient handling of different query types
- Better user experience with appropriate responses

### 4. Hybrid Approach
- Combines benefits of vector search (your specific docs) and web search (general knowledge)
- Fallback mechanisms ensure robust operation

## 🔍 Usage Examples

### Research Query
```
User: "How do I implement OAuth 2.0 authentication in a Python web app?"
System: 
1. Creates research plan
2. Generates search queries
3. Searches web for current OAuth 2.0 guides
4. Provides comprehensive answer with sources
```

### General Query
```
User: "Hello, what can you help me with?"
System: Responds directly without research
```

### Unclear Query
```
User: "What's the best way?"
System: Asks for clarification about what they want to know
```

## 🛠️ Installation

1. **Install dependencies:**
   ```bash
   pip install tavily-python
   ```

2. **Set environment variables:**
   ```bash
   export TAVILY_API_KEY=your_api_key
   ```

3. **Update your document sources** in `backend/ingest.py` if needed

4. **Run the system** - it will now use web search for research queries

## 🔧 Configuration

### Web Search Settings

You can customize web search behavior in `backend/web_search.py`:

```python
web_docs = web_search.search(
    query=state.query,
    max_results=5,          # Number of results
    search_depth="advanced", # "basic" or "advanced"
    include_answer=True,     # Include AI answer
    include_raw_content=False, # Include full HTML
    include_images=False     # Include images
)
```

### Prompt Customization

Modify prompts in `backend/retrieval_graph/prompts.py` to customize:
- Query routing logic
- Research planning approach
- Response generation style

## 🚨 Migration Notes

1. **No Breaking Changes** - The API remains the same
2. **Backward Compatible** - Vector search still works if you have ingested documents
3. **Environment Variables** - Only need to add `TAVILY_API_KEY`
4. **Gradual Migration** - Can add custom documents incrementally

## 📈 Next Steps

1. **Add Custom Documents** - Replace `load_custom_docs()` with your content sources
2. **Customize Prompts** - Tailor the system prompts for your use case
3. **Monitor Usage** - Track Tavily API usage and costs
4. **Optimize Search** - Fine-tune search parameters based on your needs