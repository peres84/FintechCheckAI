"""
PDF Downloader for downloading PDFs from URLs.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests
from backend.core.logging import log_handler


def download_pdf(source: str, output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Download PDF from URL.

    Args:
        source: URL to PDF file
        output_dir: Directory to save PDF (default: current directory)

    Returns:
        Dictionary with download results:
        {
            "file_path": str,
            "file_size": int,
            "sha256": str,
            "url": str
        }

    Raises:
        ValueError: If URL is invalid or download fails
        requests.RequestException: If HTTP request fails
    """
    log_handler.info(f"Downloading PDF from URL: {source}")

    # Validate URL
    parsed = urlparse(source)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid URL: {source}")

    # Determine output directory
    if output_dir is None:
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Download PDF
        response = requests.get(source, timeout=30, stream=True)
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

        # Save to output directory
        file_path = output_dir / filename
        file_size = 0

        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                file_size += len(chunk)

        # Calculate SHA256 hash
        import hashlib

        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        sha256 = sha256_hash.hexdigest()

        log_handler.info(
            f"PDF downloaded successfully: {file_path} ({file_size} bytes, SHA256: {sha256})"
        )

        return {
            "file_path": str(file_path),
            "file_size": file_size,
            "sha256": sha256,
            "url": source,
        }

    except requests.RequestException as e:
        error_msg = f"Failed to download PDF from {source}: {str(e)}"
        log_handler.error(error_msg)
        raise ValueError(error_msg) from e
