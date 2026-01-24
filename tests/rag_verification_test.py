"""
RAG Verification Script
Verifies claims against document chunks
"""

import json
from typing import List, Dict, Any


def hybrid_search(chunks: List[Dict[str, Any]], query: str, top_k: int = 3) -> List[Dict]:
    """
    Simple hybrid search combining keyword and semantic matching.
    In production, this would use embeddings.
    """
    results = []
    
    # Keyword matching
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    for chunk in chunks:
        content_lower = chunk['content'].lower()
        
        # Calculate keyword match score
        matches = sum(1 for word in query_words if word in content_lower)
        score = matches / len(query_words) if query_words else 0
        
        if score > 0:
            results.append({
                "chunk_id": chunk['chunk_id'],
                "page_number": chunk['page_number'],
                "score": score,
                "preview": content_lower[:100] + "...",
            })
    
    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_k]


def verify_claim(claim: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Verify a claim against document chunks.
    """
    search_results = hybrid_search(chunks, claim)
    
    verdict = "NOT_FOUND"
    if search_results and search_results[0]['score'] > 0.3:
        verdict = "FOUND_IN_DOCUMENT"
    
    return {
        "claim": claim,
        "verdict": verdict,
        "matches": len(search_results),
        "top_result": search_results[0] if search_results else None,
    }


def main():
    """Run RAG verification test."""
    # This would be loaded from Tower in production
    test_chunks = [
        {
            "chunk_id": "test-1",
            "page_number": 1,
            "content": "Duolingo reported strong user growth in Q3 2025...",
        }
    ]
    
    test_claims = [
        "Duolingo reported strong user growth in Q3 2025",
        "Revenue increased significantly",
        "New markets were entered",
    ]
    
    print("RAG Verification Results:")
    print("-" * 60)
    
    for claim in test_claims:
        result = verify_claim(claim, test_chunks)
        print(f"Claim: {result['claim']}")
        print(f"Verdict: {result['verdict']}")
        print(f"Matches: {result['matches']}")
        print()


if __name__ == "__main__":
    main()
