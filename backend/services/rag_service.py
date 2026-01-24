from __future__ import annotations

import os
from typing import Any, Optional
from pathlib import Path

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


def _tokenize(text: str) -> set[str]:
    """Tokenize text for keyword matching."""
    import re
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if token}


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


def retrieve_chunks_from_tower(
    document_id: str,
    query: str,
    top_k: int = 5,
    catalog: Optional[str] = None,
    namespace: Optional[str] = None
) -> list[dict[str, Any]]:
    """
    Retrieve chunks from Tower using RAG query.
    
    Args:
        document_id: Document ID to query chunks for
        query: Search query
        top_k: Number of top results to return
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
        
        # Use the retrieve_chunks function from rag-chunk-query app
        results = retrieve_chunks(query, filtered_chunks, top_k=top_k)
        
        log_handler.info(f"RAG query returned {len(results)} chunks")
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
            
    Returns:
        Dictionary with query and retrieved chunks
    """
    query = payload.get("query", "")
    document_id = payload.get("document_id")
    chunks = payload.get("chunks", [])
    top_k = payload.get("top_k", 5)
    
    if not query:
        return {"query": "", "chunks": [], "error": "Query is required"}
    
    # If document_id provided and Tower available, use Tower RAG
    if document_id and TOWER_RAG_AVAILABLE:
        try:
            retrieved_chunks = retrieve_chunks_from_tower(document_id, query, top_k)
            
            return {
                "query": query,
                "chunks": retrieved_chunks,
                "source": "tower"
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
            "source": "simple"
        }
    
    return {
        "query": query,
        "chunks": [],
        "source": "none",
        "error": "No chunks provided and Tower RAG unavailable"
    }
