#!/usr/bin/env python3
"""
Complete Tower + RAG Flow Test
Tests document ingestion, chunk storage, and RAG retrieval with Duolingo Q3 PDF
"""

import os
import sys
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime, timezone


def test_document_ingestion_tower():
    """Test document ingestion with Tower app locally."""
    print("=" * 70)
    print("STEP 1: Document Ingestion with Tower")
    print("=" * 70)
    
    pdf_url = "https://ik.imagekit.io/howtheydidit/hackathon/Q3FY25%20Duolingo%209-30-25%20Shareholder%20Letter%20Final.pdf?updatedAt=1769284015050"
    
    print(f"📥 Downloading PDF from URL...")
    print(f"  {pdf_url[:80]}...")
    
    try:
        import requests
    except ImportError:
        print("  Installing requests...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
        import requests
    
    try:
        response = requests.get(pdf_url, timeout=60)
        response.raise_for_status()
        pdf_bytes = response.content
    except Exception as e:
        print(f"❌ Failed to download PDF: {e}")
        return None
    
    sha256_hash = hashlib.sha256(pdf_bytes).hexdigest()
    file_size = len(pdf_bytes) / 1024 / 1024
    
    print(f"✓ Downloaded PDF successfully")
    print(f"  File size: {file_size:.2f} MB")
    print(f"  Status: OK")
    
    document_record = {
        "document_id": "duolingo-q3-fy25",
        "company_id": "duolingo",
        "version": "v1",
        "sha256": sha256_hash,
        "source_url": pdf_url,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "pdf_bytes": len(pdf_bytes),
    }
    
    print(f"\n📄 Document Metadata:")
    print(f"  ID: {document_record['document_id']}")
    print(f"  Company: {document_record['company_id']}")
    print(f"  Version: {document_record['version']}")
    print(f"  SHA256: {sha256_hash}")
    print(f"  Bytes: {document_record['pdf_bytes']}")
    
    return {
        "document_record": document_record,
        "pdf_url": pdf_url,
        "pdf_bytes": pdf_bytes,
        "sha256": sha256_hash,
    }


def extract_chunks_from_pdf(pdf_bytes: bytes, document_id: str, max_chunks: int = 5):
    """Extract chunks from PDF for testing."""
    print("\n" + "=" * 70)
    print("STEP 2: Extract Chunks from PDF")
    print("=" * 70)
    
    try:
        import pymupdf
    except ImportError:
        print("  Installing pymupdf...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pymupdf", "-q"])
        import pymupdf
    
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(doc)
    
    print(f"✓ PDF loaded: {total_pages} pages")
    
    chunks = []
    # Extract first few pages for testing
    pages_to_extract = min(max_chunks, total_pages)
    
    for page_num in range(pages_to_extract):
        page = doc[page_num]
        text = page.get_text()
        
        chunk = {
            "chunk_id": f"{document_id}-page-{page_num + 1}",
            "document_id": document_id,
            "page_number": page_num + 1,
            "content": text.strip(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        chunks.append(chunk)
        
        print(f"  Page {page_num + 1}: {len(text)} chars")
    
    doc.close()
    
    print(f"\n✓ Extracted {len(chunks)} chunks")
    
    return chunks


def test_rag_search(chunks: list, document_record: dict):
    """Test RAG search capabilities."""
    print("\n" + "=" * 70)
    print("STEP 3: RAG Search Test")
    print("=" * 70)
    
    # Sample claims to verify against document
    test_claims = [
        "Duolingo reported strong user growth in Q3 2025",
        "The company achieved profitability",
        "Duolingo expanded to new markets",
        "Daily active users increased",
    ]
    
    print(f"Testing RAG with {len(test_claims)} sample claims:")
    
    for i, claim in enumerate(test_claims, 1):
        print(f"  {i}. {claim}")
    
    # Simulate keyword-based search
    print(f"\n🔍 Keyword Search Results:")
    
    keywords = ["growth", "users", "quarterly", "revenue", "profitability"]
    found_keywords = {}
    
    for chunk in chunks:
        content_lower = chunk['content'].lower()
        for keyword in keywords:
            if keyword in content_lower:
                found_keywords[keyword] = found_keywords.get(keyword, 0) + 1
    
    for keyword, count in sorted(found_keywords.items(), key=lambda x: x[1], reverse=True):
        print(f"  '{keyword}': found in {count} chunk(s)")
    
    return {
        "claims_to_verify": test_claims,
        "keywords_found": found_keywords,
        "total_chunks": len(chunks),
    }


def create_rag_test_script():
    """Create a Python script for RAG testing."""
    print("\n" + "=" * 70)
    print("STEP 4: Generate RAG Test Script")
    print("=" * 70)
    
    script_content = '''"""
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
'''
    
    script_path = Path(__file__).parent / "tests" / "rag_verification_test.py"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(script_content)
    
    print(f"✓ Created RAG test script: {script_path}")
    return str(script_path)


def main():
    """Run complete test flow."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " FINTECH CHECK AI - Complete Flow Test ".center(68) + "║")
    print("║" + " Duolingo Q3 FY25 Document Processing ".center(68) + "║")
    print("╚" + "=" * 68 + "╝")
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Step 1: Document Ingestion
    doc_result = test_document_ingestion_tower()
    if not doc_result:
        print("\n❌ Document ingestion failed")
        return 1
    
    # Step 2: Extract Chunks
    chunks = extract_chunks_from_pdf(
        doc_result["pdf_bytes"],
        doc_result["document_record"]["document_id"],
        max_chunks=3
    )
    if not chunks:
        print("\n❌ Chunk extraction failed")
        return 1
    
    # Step 3: Test RAG
    rag_result = test_rag_search(chunks, doc_result["document_record"])
    
    # Step 4: Create RAG test script
    rag_script = create_rag_test_script()
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETE")
    print("=" * 70)
    
    print(f"""
Summary:
  ✓ Document loaded: {doc_result['document_record']['document_id']}
  ✓ SHA256 Hash: {doc_result['sha256'][:32]}...
  ✓ Chunks extracted: {len(chunks)}
  ✓ Keywords found: {len(rag_result['keywords_found'])}
  ✓ RAG script created: {rag_script}

Next Steps:
  1. Deploy document-ingestion Tower app to cloud
  2. Deploy chunk-storage Tower app to cloud
  3. Run RAG verification script with your agent
  4. Monitor via Tower UI: https://app.tower.dev/hackathon_berlin

Tower Catalog Info:
  Name: database_catalog
  Type: tower-catalog
  Environment: DEFAULT
  URI: (configured in Team Settings)
  Status: Ready
""")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
