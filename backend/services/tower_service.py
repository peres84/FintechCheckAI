from __future__ import annotations

import os
from typing import Any, Optional, Protocol
from pathlib import Path

from backend.core.logging import log_handler
from backend.core.config import config


class TowerClientLike(Protocol):
    def execute_sql(self, sql: str, params: dict[str, Any] | None = None) -> Any: ...


class TowerService:
    """Service for interacting with Tower apps and Iceberg tables."""
    
    def __init__(self, client: TowerClientLike | None = None) -> None:
        if client is None:
            try:
                from tower_sdk import TowerClient  # type: ignore
            except Exception as exc:
                raise RuntimeError(f"Tower SDK unavailable: {exc}") from exc
            client = TowerClient()
        self._client = client
        self._catalog = config.get("tower", {}).get("catalog", "database_catalog")
        self._namespace = config.get("tower", {}).get("namespace", "default")

    def insert_document(self, record: dict[str, Any]) -> Any:
        """Insert document record into Tower."""
        sql = (
            "INSERT INTO documents "
            "(document_id, company_id, version, sha256, source_url, created_at) "
            "VALUES (:document_id, :company_id, :version, :sha256, :source_url, :created_at)"
        )
        return self._client.execute_sql(sql, record)

    def insert_chunks(self, records: list[dict[str, Any]]) -> Any:
        """Insert chunk records into Tower."""
        sql = (
            "INSERT INTO chunks "
            "(chunk_id, document_id, page_number, content, embedding, created_at) "
            "VALUES (:chunk_id, :document_id, :page_number, :content, :embedding, :created_at)"
        )
        results = []
        for record in records:
            results.append(self._client.execute_sql(sql, record))
        return results
    
    def get_document(self, document_id: str) -> Optional[dict[str, Any]]:
        """Get document by ID from Tower."""
        sql = "SELECT * FROM documents WHERE document_id = :document_id LIMIT 1"
        result = self._client.execute_sql(sql, {"document_id": document_id})
        if result and len(result) > 0:
            return result[0] if isinstance(result, list) else result
        return None
    
    def get_documents_by_company(self, company_id: str) -> list[dict[str, Any]]:
        """Get all documents for a company."""
        sql = "SELECT * FROM documents WHERE company_id = :company_id ORDER BY created_at DESC"
        result = self._client.execute_sql(sql, {"company_id": company_id})
        if isinstance(result, list):
            return result
        return []
    
    def get_chunks_by_document(self, document_id: str) -> list[dict[str, Any]]:
        """Get all chunks for a document."""
        sql = "SELECT * FROM chunks WHERE document_id = :document_id ORDER BY page_number"
        result = self._client.execute_sql(sql, {"document_id": document_id})
        if isinstance(result, list):
            return result
        return []
    
    def call_document_ingestion(
        self,
        pdf_url: Optional[str] = None,
        pdf_path: Optional[str] = None,
        company_id: str = "duolingo",
        version: str = "v1",
        source_url: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Call document-ingestion Tower app.
        
        Args:
            pdf_url: URL to PDF (for remote runs)
            pdf_path: Local path to PDF (for local runs)
            company_id: Company identifier
            version: Document version
            source_url: Optional source URL
            
        Returns:
            Result from document ingestion app
        """
        try:
            import sys
            import importlib.util
            ingestion_path = Path(__file__).parent.parent / "tower" / "apps" / "document-ingestion" / "main.py"
            
            if not ingestion_path.exists():
                raise FileNotFoundError(f"Document ingestion app not found at {ingestion_path}")
            
            spec = importlib.util.spec_from_file_location("document_ingestion", ingestion_path)
            if spec and spec.loader:
                ingestion_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(ingestion_module)
                
                # Prepare event
                event = {
                    "pdf_url": pdf_url,
                    "pdf_path": pdf_path,
                    "company_id": company_id,
                    "version": version,
                    "source_url": source_url or pdf_url,
                    "catalog": self._catalog,
                    "namespace": self._namespace,
                    "dry_run": False
                }
                
                # Create writer and call handler
                writer = ingestion_module.TowerDocumentWriter(
                    catalog=self._catalog,
                    namespace=self._namespace
                )
                
                result = ingestion_module.handle_ingestion(event, writer)
                log_handler.info(f"Document ingestion completed: {result.get('document', {}).get('document_id')}")
                return result
            else:
                raise RuntimeError("Failed to load document ingestion module")
                
        except Exception as e:
            error_msg = f"Error calling document ingestion: {e}"
            log_handler.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def call_chunk_storage(
        self,
        document_id: str,
        chunks_url: Optional[str] = None,
        chunks_path: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Call chunk-storage Tower app.
        
        Args:
            document_id: Document ID to attach chunks to
            chunks_url: URL to chunks JSON (for remote runs)
            chunks_path: Local path to chunks JSON (for local runs)
            
        Returns:
            Result from chunk storage app
        """
        try:
            import sys
            import importlib.util
            chunk_storage_path = Path(__file__).parent.parent / "tower" / "apps" / "chunk-storage" / "main.py"
            
            if not chunk_storage_path.exists():
                raise FileNotFoundError(f"Chunk storage app not found at {chunk_storage_path}")
            
            spec = importlib.util.spec_from_file_location("chunk_storage", chunk_storage_path)
            if spec and spec.loader:
                chunk_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(chunk_module)
                
                # Prepare event
                event = {
                    "document_id": document_id,
                    "chunks_url": chunks_url,
                    "chunks_path": chunks_path,
                    "catalog": self._catalog,
                    "namespace": self._namespace,
                    "dry_run": False
                }
                
                # Create writer and call handler
                writer = chunk_module.TowerChunkWriter(
                    catalog=self._catalog,
                    namespace=self._namespace
                )
                
                result = chunk_module.handle_chunks(event, writer)
                log_handler.info(f"Chunk storage completed: {len(result.get('chunks', []))} chunks stored")
                return result
            else:
                raise RuntimeError("Failed to load chunk storage module")
                
        except Exception as e:
            error_msg = f"Error calling chunk storage: {e}"
            log_handler.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def call_verification_logs(
        self,
        youtube_url: str,
        company_id: str,
        verdict: str = "UNKNOWN",
        verification_id: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Call verification-logs Tower app to store verification result.
        
        Args:
            youtube_url: YouTube video URL that was verified
            company_id: Company identifier
            verdict: Verification verdict (VERIFIED, CONTRADICTED, NOT_FOUND, etc.)
            verification_id: Optional verification ID (auto-generated if not provided)
            
        Returns:
            Result from verification logs app
        """
        try:
            import sys
            import importlib.util
            verification_logs_path = Path(__file__).parent.parent / "tower" / "apps" / "verification-logs" / "main.py"
            
            if not verification_logs_path.exists():
                raise FileNotFoundError(f"Verification logs app not found at {verification_logs_path}")
            
            spec = importlib.util.spec_from_file_location("verification_logs", verification_logs_path)
            if spec and spec.loader:
                logs_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(logs_module)
                
                # Prepare event
                event = {
                    "verification_id": verification_id,
                    "youtube_url": youtube_url,
                    "company_id": company_id,
                    "verdict": verdict,
                    "catalog": self._catalog,
                    "namespace": self._namespace,
                    "dry_run": False
                }
                
                # Create store and call handler
                store = logs_module.TowerVerificationStore(
                    catalog=self._catalog,
                    namespace=self._namespace
                )
                
                result = logs_module.handle_event(event, store)
                log_handler.info(f"Verification log stored: {result.get('verification_id')}")
                return result
            else:
                raise RuntimeError("Failed to load verification logs module")
                
        except Exception as e:
            error_msg = f"Error calling verification logs: {e}"
            log_handler.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def get_verifications_by_company(self, company_id: str) -> list[dict[str, Any]]:
        """Get all verifications for a company."""
        sql = "SELECT * FROM verifications WHERE company_id = :company_id ORDER BY created_at DESC"
        result = self._client.execute_sql(sql, {"company_id": company_id})
        if isinstance(result, list):
            return result
        return []
    
    def get_verifications_by_url(self, youtube_url: str) -> list[dict[str, Any]]:
        """Get all verifications for a YouTube URL."""
        sql = "SELECT * FROM verifications WHERE youtube_url = :youtube_url ORDER BY created_at DESC"
        result = self._client.execute_sql(sql, {"youtube_url": youtube_url})
        if isinstance(result, list):
            return result
        return []
