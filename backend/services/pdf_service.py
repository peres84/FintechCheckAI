"""
PDF Service for processing PDF documents.

This service handles PDF text extraction, metadata extraction, and chunk generation.
"""

import hashlib
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests
from backend.core.logging import log_handler
from backend.etl.chunker import chunk_text
from backend.etl.normalizer import normalize_text

# Try to import PDF processor, but handle if not available
try:
    from backend.etl.pdf_processor import process_pdf
    PDF_PROCESSOR_AVAILABLE = True
except ImportError as e:
    PDF_PROCESSOR_AVAILABLE = False
    log_handler.warning(f"PDF processor not available: {e}. PDF processing will be limited.")
    
    def process_pdf(source: str, use_ocr: Optional[bool] = None) -> Dict[str, Any]:
        """Placeholder when PDF processor is not available."""
        raise RuntimeError("PDF processor not available. Install PyMuPDF (fitz) to enable PDF processing.")


class PDFService:
    """Service for processing PDF documents."""

    def __init__(self):
        """Initialize PDF service."""
        self.temp_dir = Path("temp_pdfs")
        self.temp_dir.mkdir(exist_ok=True)
        log_handler.debug("PDF Service initialized")

    def _download_pdf_from_url(self, url: str) -> Path:
        """
        Download PDF from URL to temporary location.

        Args:
            url: URL to PDF file

        Returns:
            Path to downloaded PDF file

        Raises:
            ValueError: If URL is invalid or download fails
            requests.RequestException: If HTTP request fails
        """
        log_handler.info(f"Downloading PDF from URL: {url}")

        try:
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"Invalid URL: {url}")

            # Download PDF
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get("content-type", "").lower()
            if "pdf" not in content_type:
                log_handler.warning(
                    f"Content-Type is '{content_type}', expected PDF. Proceeding anyway."
                )

            # Generate filename from URL
            filename = os.path.basename(parsed.path) or "downloaded.pdf"
            if not filename.endswith(".pdf"):
                filename += ".pdf"

            # Save to temp directory
            file_path = self.temp_dir / filename
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            log_handler.info(f"PDF downloaded to: {file_path}")
            return file_path

        except requests.RequestException as e:
            error_msg = f"Failed to download PDF from {url}: {str(e)}"
            log_handler.error(error_msg)
            raise ValueError(error_msg) from e

    def _calculate_sha256(self, file_path: Path) -> str:
        """
        Calculate SHA256 hash of PDF file.

        Args:
            file_path: Path to PDF file

        Returns:
            SHA256 hash as hex string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _extract_metadata(self, file_path: Path, pdf_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from PDF.

        Args:
            file_path: Path to PDF file
            pdf_result: Result from PDF processor

        Returns:
            Dictionary with metadata
        """
        metadata: Dict[str, Any] = {
            "file_name": file_path.name,
            "file_size": file_path.stat().st_size,
            "page_count": len(pdf_result.get("pages", [])),
            "processing_engine": pdf_result.get("engine", "unknown"),
        }

        # Try to extract PDF metadata if available
        try:
            import fitz
            doc = fitz.open(str(file_path))
            if doc.metadata:
                if doc.metadata.get("title"):
                    metadata["title"] = doc.metadata["title"]
                if doc.metadata.get("author"):
                    metadata["author"] = doc.metadata["author"]
                if doc.metadata.get("creationDate"):
                    metadata["creation_date"] = doc.metadata["creationDate"]
            doc.close()
        except Exception as e:
            log_handler.debug(f"Could not extract PDF metadata: {e}")

        return metadata

    def process_pdf(
        self,
        source: str,
        use_ocr: Optional[bool] = None,
        generate_chunks: bool = True,
        chunk_size: int = 1000,
        cleanup: bool = True,
    ) -> Dict[str, Any]:
        """
        Process PDF from URL or local path.

        Args:
            source: URL or local path to PDF file
            use_ocr: Whether to use OCR (None = auto-detect)
            generate_chunks: Whether to generate chunks from text
            chunk_size: Maximum characters per chunk
            cleanup: Whether to delete temporary files after processing

        Returns:
            Dictionary with processing results:
            {
                "sha256": str,
                "metadata": dict,
                "pages": list,
                "full_text": str,
                "chunks": list (if generate_chunks=True),
                "source": str
            }

        Raises:
            ValueError: If source is invalid or processing fails
            FileNotFoundError: If local file doesn't exist
        """
        log_handler.info(f"Processing PDF from source: {source}")

        # Determine if source is URL or local path
        is_url = source.startswith(("http://", "https://"))
        file_path: Optional[Path] = None

        try:
            if is_url:
                # Download PDF from URL
                file_path = self._download_pdf_from_url(source)
            else:
                # Use local path
                file_path = Path(source)
                if not file_path.exists():
                    raise FileNotFoundError(f"PDF file not found: {file_path}")

            # Calculate SHA256 hash
            sha256 = self._calculate_sha256(file_path)
            log_handler.debug(f"PDF SHA256: {sha256}")

            # Process PDF (extract text)
            if not PDF_PROCESSOR_AVAILABLE:
                raise RuntimeError(
                    "PDF processor not available. Install PyMuPDF (fitz) to enable PDF processing."
                )
            pdf_result = process_pdf(str(file_path), use_ocr=use_ocr)

            # Extract metadata
            metadata = self._extract_metadata(file_path, pdf_result)

            # Combine all page text
            pages = pdf_result.get("pages", [])
            full_text = "\n\n".join([page.get("text", "") for page in pages])

            # Normalize text
            normalized_text = normalize_text(full_text)

            # Generate chunks if requested
            chunks: List[Dict[str, Any]] = []
            if generate_chunks:
                chunk_texts = chunk_text(normalized_text, max_chars=chunk_size)
                chunks = [
                    {
                        "chunk_id": f"{sha256}_{i}",
                        "content": chunk,
                        "chunk_index": i,
                        "total_chunks": len(chunk_texts),
                    }
                    for i, chunk in enumerate(chunk_texts)
                ]
                log_handler.info(f"Generated {len(chunks)} chunks from PDF")

            result: Dict[str, Any] = {
                "sha256": sha256,
                "metadata": metadata,
                "pages": pages,
                "full_text": normalized_text,
                "source": source,
                "source_type": "url" if is_url else "local",
            }

            if generate_chunks:
                result["chunks"] = chunks

            log_handler.info(
                f"PDF processing complete: {metadata['page_count']} pages, "
                f"{len(chunks) if chunks else 0} chunks"
            )

            return result

        except Exception as e:
            error_msg = f"Error processing PDF from {source}: {str(e)}"
            log_handler.error(error_msg)
            raise ValueError(error_msg) from e

        finally:
            # Cleanup temporary file if downloaded
            if cleanup and is_url and file_path and file_path.exists():
                try:
                    file_path.unlink()
                    log_handler.debug(f"Cleaned up temporary file: {file_path}")
                except Exception as e:
                    log_handler.warning(f"Failed to cleanup temporary file: {e}")

    def process_pdf_from_bytes(
        self,
        pdf_bytes: bytes,
        filename: str = "uploaded.pdf",
        use_ocr: Optional[bool] = None,
        generate_chunks: bool = True,
        chunk_size: int = 1000,
    ) -> Dict[str, Any]:
        """
        Process PDF from bytes (e.g., file upload).

        Args:
            pdf_bytes: PDF file content as bytes
            filename: Original filename
            use_ocr: Whether to use OCR (None = auto-detect)
            generate_chunks: Whether to generate chunks from text
            chunk_size: Maximum characters per chunk

        Returns:
            Dictionary with processing results (same as process_pdf)

        Raises:
            ValueError: If processing fails
        """
        log_handler.info(f"Processing PDF from bytes ({len(pdf_bytes)} bytes)")

        # Save bytes to temporary file
        temp_file = self.temp_dir / filename
        try:
            with open(temp_file, "wb") as f:
                f.write(pdf_bytes)

            # Process using local path method
            result = self.process_pdf(
                str(temp_file),
                use_ocr=use_ocr,
                generate_chunks=generate_chunks,
                chunk_size=chunk_size,
                cleanup=True,  # Always cleanup temp file
            )

            # Update source info
            result["source"] = filename
            result["source_type"] = "upload"

            return result

        except Exception as e:
            error_msg = f"Error processing PDF from bytes: {str(e)}"
            log_handler.error(error_msg)
            raise ValueError(error_msg) from e


# Create singleton instance
pdf_service = PDFService()


# Backward compatibility function
def process_pdf(source: str) -> Dict[str, Any]:
    """
    Process PDF from URL or local path (backward compatibility).

    Args:
        source: URL or local path to PDF file

    Returns:
        Dictionary with processing results
    """
    return pdf_service.process_pdf(source)
