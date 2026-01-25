from __future__ import annotations

import os
from typing import Any, Literal, Optional
from pathlib import Path

import numpy as np

# Import logging
from backend.core.logging import log_handler
from backend.core.config import config

# Try to import Tower app handlers
try:
    import sys
    import importlib.util
    rag_query_path = Path(__file__).parent.parent.parent / "tower" / "apps" / "rag-chunk-query" / "main.py"
    
    if rag_query_path.exists():
        spec = importlib.util.spec_from_file_location("rag_chunk_query", rag_query_path)
        if spec and spec.loader:
            rag_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(rag_module)
            TowerChunkStore = rag_module.TowerChunkStore  # type: ignore
            retrieve_chunks = rag_module.retrieve_chunks  # type: ignore
            TOWER_RAG_AVAILABLE = True
        else:
            TOWER_RAG_AVAILABLE = False
    else:
        TOWER_RAG_AVAILABLE = False
except (ImportError, Exception) as e:
    TOWER_RAG_AVAILABLE = False
    log_handler.warning(f"Tower RAG app not available: {e}. RAG service will use fallback implementation.")


# Try to import OpenAI for embeddings
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    log_handler.warning("OpenAI not available. Semantic search will be disabled.")


def _tokenize(text: str) -> set[str]:
    """Tokenize text for keyword matching."""
    import re
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if token}


def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score (0-1)
    """
    try:
        v1 = np.array(vec1, dtype=np.float32)
        v2 = np.array(vec2, dtype=np.float32)
        
        # Handle empty vectors
        if len(v1) == 0 or len(v2) == 0:
            return 0.0
        
        # Ensure same length
        if len(v1) != len(v2):
            min_len = min(len(v1), len(v2))
            v1 = v1[:min_len]
            v2 = v2[:min_len]
        
        # Calculate cosine similarity
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    except Exception as e:
        log_handler.warning(f"Error calculating cosine similarity: {e}")
        return 0.0


async def _get_query_embedding(query: str) -> Optional[list[float]]:
    """
    Generate embedding for query text using OpenAI.
    
    Args:
        query: Query text
        
    Returns:
        Embedding vector or None if unavailable
    """
    if not OPENAI_AVAILABLE:
        return None
    
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            log_handler.warning("OPENAI_API_KEY not set. Semantic search disabled.")
            return None
        
        client = AsyncOpenAI(api_key=api_key)
        
        # Use text-embedding-3-small for cost efficiency
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        
        embedding = response.data[0].embedding
        log_handler.debug(f"Generated embedding for query (dimension: {len(embedding)})")
        return embedding
        
    except Exception as e:
        log_handler.warning(f"Failed to generate query embedding: {e}")
        return None


def retrieve_chunks_simple(query: str, chunks: list[dict[str, Any]], top_k: int = 5) -> list[dict[str, Any]]:
    """
    Simple keyword-based chunk retrieval (fallback).
    
    Args:
        query: Search query
        chunks: List of chunks to search
        top_k: Number of top results to return
        
    Returns:
        List of top-k chunks with scores
    """
    query_tokens = _tokenize(query)
    scored = []
    for chunk in chunks:
        chunk_tokens = _tokenize(chunk.get("content", ""))
        if not chunk_tokens:
            score = 0.0
        else:
            score = len(query_tokens & chunk_tokens) / max(len(query_tokens), 1)
        scored.append({**chunk, "score": score})

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


def retrieve_chunks_semantic(
    query_embedding: list[float],
    chunks: list[dict[str, Any]],
    top_k: int = 5
) -> list[dict[str, Any]]:
    """
    Retrieve chunks using semantic similarity (cosine similarity on embeddings).
    
    Args:
        query_embedding: Query embedding vector
        chunks: List of chunks with embeddings
        top_k: Number of top results to return
        
    Returns:
        List of top-k chunks with similarity scores
    """
    if not query_embedding:
        log_handler.warning("No query embedding provided for semantic search")
        return []
    
    scored = []
    for chunk in chunks:
        chunk_embedding = chunk.get("embedding")
        
        # Skip chunks without embeddings
        if not chunk_embedding or not isinstance(chunk_embedding, list):
            continue
        
        # Calculate cosine similarity
        similarity = _cosine_similarity(query_embedding, chunk_embedding)
        scored.append({**chunk, "score": similarity, "similarity": similarity})
    
    # Sort by similarity score (descending)
    scored.sort(key=lambda item: item["score"], reverse=True)
    
    log_handler.debug(f"Semantic search found {len(scored)} chunks with embeddings")
    return scored[:top_k]


def retrieve_chunks_hybrid(
    query: str,
    query_embedding: Optional[list[float]],
    chunks: list[dict[str, Any]],
    top_k: int = 5,
    semantic_weight: float = 0.7,
    keyword_weight: float = 0.3
) -> list[dict[str, Any]]:
    """
    Retrieve chunks using hybrid search (semantic + keyword).
    
    Args:
        query: Search query text
        query_embedding: Query embedding vector (optional)
        chunks: List of chunks to search
        top_k: Number of top results to return
        semantic_weight: Weight for semantic score (default: 0.7)
        keyword_weight: Weight for keyword score (default: 0.3)
        
    Returns:
        List of top-k chunks with combined scores
    """
    # Normalize weights
    total_weight = semantic_weight + keyword_weight
    if total_weight > 0:
        semantic_weight = semantic_weight / total_weight
        keyword_weight = keyword_weight / total_weight
    
    # Get semantic scores
    semantic_scores = {}
    if query_embedding:
        semantic_results = retrieve_chunks_semantic(query_embedding, chunks, top_k=len(chunks))
        for result in semantic_results:
            chunk_id = result.get("chunk_id") or str(hash(result.get("content", "")))
            semantic_scores[chunk_id] = result["score"]
    
    # Get keyword scores
    keyword_results = retrieve_chunks_simple(query, chunks, top_k=len(chunks))
    keyword_scores = {}
    for result in keyword_results:
        chunk_id = result.get("chunk_id") or str(hash(result.get("content", "")))
        keyword_scores[chunk_id] = result["score"]
    
    # Normalize scores to 0-1 range
    if semantic_scores:
        max_semantic = max(semantic_scores.values()) if semantic_scores.values() else 1.0
        if max_semantic > 0:
            semantic_scores = {k: v / max_semantic for k, v in semantic_scores.items()}
    
    if keyword_scores:
        max_keyword = max(keyword_scores.values()) if keyword_scores.values() else 1.0
        if max_keyword > 0:
            keyword_scores = {k: v / max_keyword for k, v in keyword_scores.items()}
    
    # Combine scores
    combined_scores = {}
    all_chunk_ids = set(semantic_scores.keys()) | set(keyword_scores.keys())
    
    for chunk_id in all_chunk_ids:
        semantic_score = semantic_scores.get(chunk_id, 0.0) if query_embedding else 0.0
        keyword_score = keyword_scores.get(chunk_id, 0.0)
        
        combined_score = (semantic_score * semantic_weight) + (keyword_score * keyword_weight)
        combined_scores[chunk_id] = combined_score
    
    # Map back to chunks with combined scores
    chunk_map = {chunk.get("chunk_id") or str(hash(chunk.get("content", ""))): chunk for chunk in chunks}
    
    scored_chunks = []
    for chunk_id, score in combined_scores.items():
        if chunk_id in chunk_map:
            chunk = chunk_map[chunk_id]
            scored_chunks.append({
                **chunk,
                "score": score,
                "semantic_score": semantic_scores.get(chunk_id, 0.0) if query_embedding else None,
                "keyword_score": keyword_scores.get(chunk_id, 0.0)
            })
    
    # Sort by combined score
    scored_chunks.sort(key=lambda item: item["score"], reverse=True)
    
    log_handler.debug(
        f"Hybrid search: semantic_weight={semantic_weight:.2f}, "
        f"keyword_weight={keyword_weight:.2f}, found {len(scored_chunks)} chunks"
    )
    return scored_chunks[:top_k]


async def retrieve_chunks_from_tower(
    document_id: str,
    query: str,
    top_k: int = 5,
    search_method: Literal["keyword", "semantic", "hybrid"] = "hybrid",
    catalog: Optional[str] = None,
    namespace: Optional[str] = None
) -> list[dict[str, Any]]:
    """
    Retrieve chunks from Tower using RAG query with configurable search method.
    
    Args:
        document_id: Document ID to query chunks for
        query: Search query
        top_k: Number of top results to return
        search_method: Search method - "keyword", "semantic", or "hybrid" (default: "hybrid")
        catalog: Tower catalog name (defaults from config)
        namespace: Tower namespace (defaults from config)
        
    Returns:
        List of top-k chunks with scores
    """
    if not TOWER_RAG_AVAILABLE:
        log_handler.warning("Tower RAG not available, using simple retrieval")
        return []
    
    try:
        catalog_name = catalog or config.get("tower", {}).get("catalog", "database_catalog")
        namespace_name = namespace or config.get("tower", {}).get("namespace", "default")
        
        # Create Tower chunk store
        store = TowerChunkStore(catalog=catalog_name, namespace=namespace_name)
        
        # Read all chunks from Tower
        all_chunks = store.read_all()
        
        # Filter by document_id if provided
        if document_id:
            filtered_chunks = [
                chunk for chunk in all_chunks 
                if chunk.get("document_id") == document_id
            ]
        else:
            filtered_chunks = all_chunks
        
        log_handler.debug(f"Found {len(filtered_chunks)} chunks for document {document_id}")
        
        # Determine search method
        if search_method == "keyword":
            # Use simple keyword matching
            results = retrieve_chunks_simple(query, filtered_chunks, top_k=top_k)
            log_handler.info(f"Keyword search returned {len(results)} chunks")
            
        elif search_method == "semantic":
            # Use semantic search only
            query_embedding = await _get_query_embedding(query)
            if not query_embedding:
                log_handler.warning("Semantic search failed, falling back to keyword")
                results = retrieve_chunks_simple(query, filtered_chunks, top_k=top_k)
            else:
                results = retrieve_chunks_semantic(query_embedding, filtered_chunks, top_k=top_k)
                log_handler.info(f"Semantic search returned {len(results)} chunks")
                
        else:  # hybrid (default)
            # Use hybrid search
            query_embedding = await _get_query_embedding(query)
            if not query_embedding:
                log_handler.warning("Hybrid search: no embedding, using keyword only")
                results = retrieve_chunks_simple(query, filtered_chunks, top_k=top_k)
            else:
                # Get weights from config or use defaults
                semantic_weight = config.get("rag", {}).get("semantic_weight", 0.7)
                keyword_weight = config.get("rag", {}).get("keyword_weight", 0.3)
                results = retrieve_chunks_hybrid(
                    query,
                    query_embedding,
                    filtered_chunks,
                    top_k=top_k,
                    semantic_weight=semantic_weight,
                    keyword_weight=keyword_weight
                )
                log_handler.info(f"Hybrid search returned {len(results)} chunks")
        
        return results
        
    except Exception as e:
        error_msg = f"Error retrieving chunks from Tower: {e}"
        log_handler.error(error_msg)
        # Fallback to empty list
        return []


def verify_claims(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Verify claims using RAG retrieval.
    
    Args:
        payload: Dictionary containing:
            - query: Search query (claim text)
            - document_id: Optional document ID for Tower query
            - chunks: Optional list of chunks (for fallback)
            - top_k: Number of results (default: 5)
            - search_method: "keyword", "semantic", or "hybrid" (default: "hybrid")
            
    Returns:
        Dictionary with query and retrieved chunks
    """
    query = payload.get("query", "")
    document_id = payload.get("document_id")
    chunks = payload.get("chunks", [])
    top_k = payload.get("top_k", 5)
    search_method = payload.get("search_method", "hybrid")
    
    if not query:
        return {"query": "", "chunks": [], "error": "Query is required"}
    
    # If document_id provided and Tower available, use Tower RAG
    if document_id and TOWER_RAG_AVAILABLE:
        try:
            # Note: This is async but verify_claims is sync - need to handle this
            # For now, we'll use the sync version or make this async
            import asyncio
            retrieved_chunks = asyncio.run(
                retrieve_chunks_from_tower(document_id, query, top_k, search_method)
            )
            
            return {
                "query": query,
                "chunks": retrieved_chunks,
                "source": "tower",
                "search_method": search_method
            }
        except Exception as e:
            log_handler.warning(f"Tower RAG failed, falling back to simple retrieval: {e}")
            # Fall through to simple retrieval
    
    # Fallback to simple keyword matching
    if chunks:
        retrieved_chunks = retrieve_chunks_simple(query, chunks, top_k)
        return {
            "query": query,
            "chunks": retrieved_chunks,
            "source": "simple",
            "search_method": "keyword"
        }
    
    return {
        "query": query,
        "chunks": [],
        "source": "none",
        "error": "No chunks provided and Tower RAG unavailable"
    }
