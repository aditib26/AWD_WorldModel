"""
RAG Client for AWD Assistant
Integrates Qdrant vector database for retrieving handbook context
"""

import os
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from openai import AsyncOpenAI

load_dotenv()

# Environment variables
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "one_million_hectare")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Global clients
_qdrant_client: Optional[QdrantClient] = None
_openai_client: Optional[AsyncOpenAI] = None
_qdrant_available: bool = False
_openai_available: bool = False

# Embedding model
EMBED_MODEL = "text-embedding-3-small"

# Timeouts (in seconds)
QDRANT_INIT_TIMEOUT = 10
QDRANT_SEARCH_TIMEOUT = 15
OPENAI_EMBED_TIMEOUT = 10


def get_qdrant_client() -> Optional[QdrantClient]:
    """Initialize and return Qdrant client (singleton pattern)"""
    global _qdrant_client, _qdrant_available
    
    if _qdrant_client is not None:
        return _qdrant_client if _qdrant_available else None
    
    if not QDRANT_URL or not QDRANT_API_KEY:
        print("⚠️ AWD Assistant: RAG disabled - Missing QDRANT_URL or QDRANT_API_KEY in environment")
        _qdrant_available = False
        return None
    
    try:
        print(f"🔄 AWD Assistant: Connecting to Qdrant at {QDRANT_URL}...")
        _qdrant_client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            timeout=QDRANT_INIT_TIMEOUT
        )
        
        # Health check - verify collection exists
        try:
            collection_info = _qdrant_client.get_collection(collection_name=COLLECTION_NAME)
            _qdrant_available = True
            print(f"✅ AWD Assistant: Qdrant client initialized for collection: {COLLECTION_NAME} ({collection_info.points_count} points)")
            return _qdrant_client
        except Exception as health_err:
            print(f"⚠️ AWD Assistant: Qdrant connected but collection '{COLLECTION_NAME}' not found: {health_err}")
            _qdrant_available = False
            return None
            
    except Exception as e:
        print(f"❌ AWD Assistant: Failed to connect to Qdrant: {e}")
        _qdrant_available = False
        return None


def get_openai_client() -> Optional[AsyncOpenAI]:
    """Initialize and return OpenAI client for embeddings (singleton pattern)"""
    global _openai_client, _openai_available
    
    if _openai_client is not None:
        return _openai_client if _openai_available else None
    
    if not OPENAI_API_KEY:
        print("⚠️ AWD Assistant: RAG disabled - Missing OPENAI_API_KEY for embeddings")
        _openai_available = False
        return None
    
    try:
        _openai_client = AsyncOpenAI(
            api_key=OPENAI_API_KEY,
            timeout=OPENAI_EMBED_TIMEOUT
        )
        _openai_available = True
        return _openai_client
    except Exception as e:
        print(f"❌ AWD Assistant: Failed to initialize OpenAI client: {e}")
        _openai_available = False
        return None


async def embed_text(text: str) -> Optional[List[float]]:
    """Generate embedding vector for the given text using OpenAI"""
    client = get_openai_client()
    if not client:
        return None
    
    try:
        import asyncio
        response = await asyncio.wait_for(
            client.embeddings.create(
                model=EMBED_MODEL,
                input=text[:8000]  # Limit input length
            ),
            timeout=OPENAI_EMBED_TIMEOUT
        )
        return response.data[0].embedding
    except asyncio.TimeoutError:
        print(f"⚠️ AWD Assistant: OpenAI embedding timeout after {OPENAI_EMBED_TIMEOUT}s")
        return None
    except Exception as e:
        print(f"❌ AWD Assistant: Embedding error: {e}")
        return None


async def retrieve_context(query: str, top_k: int = 3) -> Dict[str, Any]:
    """
    Retrieve relevant chunks from Qdrant and format them as context
    
    Args:
        query: User's question
        top_k: Number of chunks to retrieve
        
    Returns:
        Dictionary containing formatted context text and metadata
    """
    # Try to get client (will initialize on first call and set availability flags)
    client = get_qdrant_client()
    if not client:
        return {"context_text": "", "citations": []}
    
    # Generate embedding
    print(f"🔍 AWD Assistant: RAG search query: '{query[:100]}...'")
    query_vector = await embed_text(query)
    if not query_vector:
        print("⚠️ AWD Assistant: Could not generate embedding for RAG search")
        return {"context_text": "", "citations": []}
    
    try:
        # Search Qdrant with timeout
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        def sync_search():
            return client.query_points(
                collection_name=COLLECTION_NAME,
                query=query_vector,
                limit=top_k,
                timeout=QDRANT_SEARCH_TIMEOUT
            )
        
        # Run sync Qdrant call in thread pool with timeout
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            search_result = await asyncio.wait_for(
                loop.run_in_executor(pool, sync_search),
                timeout=QDRANT_SEARCH_TIMEOUT + 2
            )
        
        if not search_result.points:
            print("⚠️ AWD Assistant: No relevant documents found in RAG search")
            return {"context_text": "", "citations": []}
        
        # Log scores to diagnose relevance
        scores = [f"{h.score:.3f}" for h in search_result.points[:3]]
        print(f"✅ AWD Assistant: Retrieved {len(search_result.points)} documents (scores: {scores})")
        
        # Filter by score threshold (only keep relevant results)
        SCORE_THRESHOLD = 0.35  # Lowered due to collection quality - adjust based on results
        filtered_points = [hit for hit in search_result.points if hit.score >= SCORE_THRESHOLD]
        
        if not filtered_points:
            print(f"⚠️ AWD Assistant: No results above score threshold {SCORE_THRESHOLD} (top score: {search_result.points[0].score:.3f})")
            return {"context_text": "", "citations": []}
        
        print(f"✅ AWD Assistant: {len(filtered_points)} results above threshold {SCORE_THRESHOLD}")
        
        # Format context and citations
        context_parts = []
        citations = []
        
        for i, hit in enumerate(filtered_points, 1):
            payload = hit.payload
            
            # Build context string (match RA_Backend structure)
            chunk_text = payload.get("content", "")
            title = payload.get("title", "")
            chapter = payload.get("chapter_title", "")
            section = payload.get("section_title", "")
            chunk_id = payload.get("chunk_id", f"Chunk {i}")
            
            # Format context entry with metadata
            source_label = title or chapter or section or chunk_id
            context_entry = f"[Source {i}] {source_label}\n{chunk_text}\n(Relevance: {hit.score:.3f})"
            context_parts.append(context_entry)
            
            # Store citation metadata
            citations.append({
                "id": i,
                "title": title,
                "chapter_title": chapter,
                "section_title": section,
                "chunk_id": chunk_id,
                "content": chunk_text,
                "score": hit.score,
                "summary": payload.get("summary", "")
            })
        
        print(f"✅ AWD Assistant: Retrieved {len(citations)} relevant documents from RAG")
        return {
            "context_text": "\n\n".join(context_parts),
            "citations": citations
        }
        
    except asyncio.TimeoutError:
        print(f"⚠️ AWD Assistant: RAG search timeout after {QDRANT_SEARCH_TIMEOUT}s - continuing without handbook context")
        return {"context_text": "", "citations": []}
    except Exception as e:
        # Graceful degradation - system continues without RAG
        # Common errors: ResponseHandlingException, ConnectionError, TimeoutError
        error_name = type(e).__name__
        error_msg = str(e)
        print(f"⚠️ AWD Assistant: RAG search error ({error_name}): {error_msg[:100]} - continuing without handbook context")
        return {"context_text": "", "citations": []}
