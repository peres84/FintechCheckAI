"""
Tests for PDF Service.
"""

import hashlib
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from backend.services.pdf_service import PDFService, pdf_service


class TestPDFService:
    """Test PDF Service functionality."""

    def test_init(self):
        """Test PDF service initialization."""
        service = PDFService()
        assert service.temp_dir.exists()
        assert service.temp_dir.name == "temp_pdfs"

    def test_calculate_sha256(self, tmp_path):
        """Test SHA256 hash calculation."""
        service = PDFService()
        
        # Create a test file
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"test content")
        
        sha256 = service._calculate_sha256(test_file)
        
        # Verify it's a valid SHA256 hash (64 hex characters)
        assert len(sha256) == 64
        assert all(c in "0123456789abcdef" for c in sha256)
        
        # Verify it's correct
        expected = hashlib.sha256(b"test content").hexdigest()
        assert sha256 == expected

    @patch("backend.services.pdf_service.requests.get")
    def test_download_pdf_from_url_success(self, mock_get, tmp_path):
        """Test successful PDF download from URL."""
        service = PDFService()
        service.temp_dir = tmp_path
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.iter_content.return_value = [b"PDF content"]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        url = "https://example.com/test.pdf"
        result = service._download_pdf_from_url(url)
        
        assert result.exists()
        assert result.name == "test.pdf"
        mock_get.assert_called_once()

    @patch("backend.services.pdf_service.requests.get")
    def test_download_pdf_from_url_invalid(self, mock_get):
        """Test PDF download with invalid URL."""
        service = PDFService()
        
        with pytest.raises(ValueError, match="Invalid URL"):
            service._download_pdf_from_url("not-a-url")

    @patch("backend.services.pdf_service.requests.get")
    def test_download_pdf_from_url_failure(self, mock_get):
        """Test PDF download failure."""
        service = PDFService()
        
        import requests
        mock_get.side_effect = requests.RequestException("Network error")
        
        with pytest.raises(ValueError, match="Failed to download"):
            service._download_pdf_from_url("https://example.com/test.pdf")

    def test_extract_metadata(self, tmp_path):
        """Test metadata extraction."""
        service = PDFService()
        
        # Create a dummy file
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"dummy")
        
        pdf_result = {
            "engine": "hybrid",
            "pages": [
                {"page": 1, "text": "Page 1", "source": "text"},
                {"page": 2, "text": "Page 2", "source": "text"},
            ],
        }
        
        metadata = service._extract_metadata(test_file, pdf_result)
        
        assert metadata["file_name"] == "test.pdf"
        assert metadata["file_size"] == 5
        assert metadata["page_count"] == 2
        assert metadata["processing_engine"] == "hybrid"

    @patch("backend.services.pdf_service.PDF_PROCESSOR_AVAILABLE", True)
    @patch("backend.services.pdf_service.process_pdf")
    def test_process_pdf_local_path(self, mock_process_pdf, tmp_path):
        """Test processing PDF from local path."""
        service = PDFService()
        
        # Create actual test file
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"dummy pdf content")
        
        mock_process_pdf.return_value = {
            "engine": "hybrid",
            "pages": [{"page": 1, "text": "Test", "source": "text"}],
        }
        
        result = service.process_pdf(str(test_file), generate_chunks=False)
        
        assert "sha256" in result
        assert len(result["sha256"]) == 64
        assert "metadata" in result
        assert "pages" in result
        assert "full_text" in result
        assert result["source_type"] == "local"

    @patch("backend.services.pdf_service.PDF_PROCESSOR_AVAILABLE", True)
    @patch("backend.services.pdf_service.process_pdf")
    @patch("backend.services.pdf_service.PDFService._download_pdf_from_url")
    def test_process_pdf_from_url(self, mock_download, mock_process_pdf, tmp_path):
        """Test processing PDF from URL."""
        service = PDFService()
        service.temp_dir = tmp_path
        
        test_file = tmp_path / "downloaded.pdf"
        test_file.write_bytes(b"dummy")
        mock_download.return_value = test_file
        
        mock_process_pdf.return_value = {
            "engine": "hybrid",
            "pages": [{"page": 1, "text": "Test", "source": "text"}],
        }
        
        with patch("backend.services.pdf_service.Path.stat") as mock_stat:
            mock_stat.return_value = Mock(st_size=1000)
            
            with patch("backend.services.pdf_service.hashlib.sha256") as mock_sha:
                mock_sha.return_value.hexdigest.return_value = "abc123"
                mock_sha.return_value.update = Mock()
                
                result = service.process_pdf(
                    "https://example.com/test.pdf",
                    generate_chunks=False,
                    cleanup=True,
                )
                
                assert result["source_type"] == "url"
                mock_download.assert_called_once()

    def test_process_pdf_from_bytes(self, tmp_path):
        """Test processing PDF from bytes."""
        service = PDFService()
        service.temp_dir = tmp_path
        
        pdf_bytes = b"dummy pdf content"
        
        with patch("backend.services.pdf_service.PDFService.process_pdf") as mock_process:
            mock_process.return_value = {
                "sha256": "abc123",
                "metadata": {"file_name": "test.pdf"},
                "pages": [],
                "full_text": "Test",
                "source": str(tmp_path / "test.pdf"),
                "source_type": "local",
            }
            
            result = service.process_pdf_from_bytes(
                pdf_bytes, filename="test.pdf", generate_chunks=False
            )
            
            assert result["source"] == "test.pdf"
            assert result["source_type"] == "upload"

    def test_process_pdf_file_not_found(self):
        """Test processing non-existent PDF file."""
        service = PDFService()
        
        with pytest.raises((ValueError, FileNotFoundError), match="(Error processing PDF|not found)"):
            service.process_pdf("/nonexistent/file.pdf")

    def test_backward_compatibility_function(self):
        """Test backward compatibility function."""
        with patch("backend.services.pdf_service.pdf_service.process_pdf") as mock_process:
            mock_process.return_value = {"sha256": "abc123"}
            
            from backend.services.pdf_service import process_pdf
            
            result = process_pdf("test.pdf")
            assert result["sha256"] == "abc123"


class TestPDFServiceIntegration:
    """Integration tests for PDF service (requires actual PDF file and dependencies)."""

    @pytest.mark.skipif(
        not Path("docs/Q3FY25 Duolingo 9-30-25 Shareholder Letter Final.pdf").exists(),
        reason="Test PDF not found",
    )
    @pytest.mark.skipif(
        not hasattr(__import__("backend.services.pdf_service", fromlist=["PDF_PROCESSOR_AVAILABLE"]), "PDF_PROCESSOR_AVAILABLE") or 
        not __import__("backend.services.pdf_service", fromlist=["PDF_PROCESSOR_AVAILABLE"]).PDF_PROCESSOR_AVAILABLE,
        reason="PDF processor not available (fitz/PyMuPDF not installed)",
    )
    def test_process_pdf_real_file(self):
        """Test processing a real PDF file."""
        service = PDFService()
        
        pdf_path = "docs/Q3FY25 Duolingo 9-30-25 Shareholder Letter Final.pdf"
        result = service.process_pdf(pdf_path, generate_chunks=True, chunk_size=500)
        
        assert "sha256" in result
        assert len(result["sha256"]) == 64
        assert "metadata" in result
        assert "pages" in result
        assert len(result["pages"]) > 0
        assert "full_text" in result
        assert len(result["full_text"]) > 0
        assert "chunks" in result
        assert len(result["chunks"]) > 0
        assert result["source_type"] == "local"
