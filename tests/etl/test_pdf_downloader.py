"""
Tests for PDF Downloader.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from backend.etl.pdf_downloader import download_pdf


class TestPDFDownloader:
    """Test PDF downloader functionality."""

    @patch("backend.etl.pdf_downloader.requests.get")
    def test_download_pdf_success(self, mock_get, tmp_path):
        """Test successful PDF download."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.iter_content.return_value = [b"PDF content"]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        url = "https://example.com/test.pdf"
        result = download_pdf(url, output_dir=tmp_path)
        
        assert "file_path" in result
        assert "file_size" in result
        assert "sha256" in result
        assert "url" in result
        assert result["url"] == url
        assert Path(result["file_path"]).exists()
        assert len(result["sha256"]) == 64

    @patch("backend.etl.pdf_downloader.requests.get")
    def test_download_pdf_wrong_content_type(self, mock_get, tmp_path):
        """Test download with wrong content type (should still work with warning)."""
        mock_response = Mock()
        mock_response.headers = {"content-type": "text/html"}
        mock_response.iter_content.return_value = [b"PDF content"]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        url = "https://example.com/test.pdf"
        result = download_pdf(url, output_dir=tmp_path)
        
        # Should still download despite wrong content type
        assert result["file_path"]
        assert Path(result["file_path"]).exists()

    def test_download_pdf_invalid_url(self):
        """Test download with invalid URL."""
        with pytest.raises(ValueError, match="Invalid URL"):
            download_pdf("not-a-url")

    @patch("backend.etl.pdf_downloader.requests.get")
    def test_download_pdf_network_error(self, mock_get):
        """Test download with network error."""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")
        
        with pytest.raises(ValueError, match="Failed to download"):
            download_pdf("https://example.com/test.pdf")

    @patch("backend.etl.pdf_downloader.requests.get")
    def test_download_pdf_http_error(self, mock_get):
        """Test download with HTTP error."""
        import requests
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        with pytest.raises(ValueError, match="Failed to download"):
            download_pdf("https://example.com/test.pdf")
