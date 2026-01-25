"""
Tests for Documents API endpoints.
"""

import io
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient

# Mock TowerService before importing app
with patch("backend.services.tower_service.TowerService") as mock_tower_class:
    mock_tower_instance = MagicMock()
    mock_tower_class.return_value = mock_tower_instance
    
    from backend.main import app

client = TestClient(app)


class TestDocumentsAPI:
    """Test documents API endpoints."""

    @patch("backend.api.routes.documents.get_tower_service")
    def test_upload_document_json_url(self, mock_get_tower):
        """Test document upload with JSON body and URL."""
        mock_tower = MagicMock()
        mock_tower.call_document_ingestion.return_value = {
            "document": {"document_id": "test-doc-123"}
        }
        mock_get_tower.return_value = mock_tower
        
        response = client.post(
            "/api/documents/json",
            json={
                "company_id": "duolingo",
                "pdf_url": "https://example.com/document.pdf"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "test-doc-123"
        assert data["status"] == "completed"
        mock_tower.call_document_ingestion.assert_called_once()

    def test_upload_document_json_missing_company_id(self):
        """Test document upload with missing company_id."""
        response = client.post(
            "/api/documents/json",
            json={"pdf_url": "https://example.com/document.pdf"}
        )
        
        assert response.status_code == 422  # Validation error

    def test_upload_document_json_missing_url(self):
        """Test document upload with missing pdf_url."""
        response = client.post(
            "/api/documents/json",
            json={"company_id": "duolingo"}
        )
        
        assert response.status_code == 400
        assert "pdf_url is required" in response.json()["detail"]

    @patch("backend.api.routes.documents.pdf_service")
    @patch("backend.api.routes.documents._upload_pdf_to_imagekit")
    @patch("backend.api.routes.documents.get_tower_service")
    @patch("backend.api.routes.documents._delete_from_imagekit")
    def test_upload_document_file(
        self,
        mock_delete,
        mock_get_tower,
        mock_upload_imagekit,
        mock_pdf_service
    ):
        """Test document upload with file."""
        # Mock PDF processing
        mock_pdf_service.process_pdf_from_bytes.return_value = {
            "sha256": "abc123",
            "metadata": {"page_count": 10, "file_name": "test.pdf"},
            "pages": [],
            "full_text": "Test content"
        }
        
        # Mock ImageKit upload
        mock_upload_imagekit.return_value = (
            "https://ik.imagekit.io/test/document.pdf",
            "file-id-123"
        )
        
        # Mock Tower service
        mock_tower = MagicMock()
        mock_tower.call_document_ingestion.return_value = {
            "document": {"document_id": "test-doc-456"}
        }
        mock_get_tower.return_value = mock_tower
        
        # Create test PDF file
        pdf_content = b"%PDF-1.4\nTest PDF content"
        files = {
            "pdf_file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")
        }
        data = {
            "company_id": "duolingo",
            "version": "v1"
        }
        
        response = client.post(
            "/api/documents",
            files=files,
            data=data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "test-doc-456"
        assert data["status"] == "completed"
        
        # Verify cleanup was called
        mock_delete.assert_called_once_with("file-id-123")

    def test_upload_document_file_invalid_type(self):
        """Test document upload with non-PDF file."""
        files = {
            "pdf_file": ("test.txt", io.BytesIO(b"Not a PDF"), "text/plain")
        }
        data = {"company_id": "duolingo"}
        
        response = client.post(
            "/api/documents",
            files=files,
            data=data
        )
        
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    def test_upload_document_file_too_large(self):
        """Test document upload with file exceeding size limit."""
        # Create a large file (over 50MB)
        large_content = b"x" * (51 * 1024 * 1024)  # 51MB
        
        files = {
            "pdf_file": ("large.pdf", io.BytesIO(large_content), "application/pdf")
        }
        data = {"company_id": "duolingo"}
        
        response = client.post(
            "/api/documents",
            files=files,
            data=data
        )
        
        assert response.status_code == 400
        assert "size" in response.json()["detail"].lower()

    def test_upload_document_file_empty(self):
        """Test document upload with empty file."""
        files = {
            "pdf_file": ("empty.pdf", io.BytesIO(b""), "application/pdf")
        }
        data = {"company_id": "duolingo"}
        
        response = client.post(
            "/api/documents",
            files=files,
            data=data
        )
        
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_upload_document_missing_both(self):
        """Test document upload with neither file nor URL."""
        data = {"company_id": "duolingo"}
        
        response = client.post(
            "/api/documents",
            data=data
        )
        
        assert response.status_code == 400
        assert "pdf_file or pdf_url" in response.json()["detail"]

    @patch("backend.api.routes.documents.get_tower_service")
    def test_upload_document_url_form_data(self, mock_get_tower):
        """Test document upload with URL via form data."""
        mock_tower = MagicMock()
        mock_tower.call_document_ingestion.return_value = {
            "document": {"document_id": "test-doc-789"}
        }
        mock_get_tower.return_value = mock_tower
        
        data = {
            "company_id": "duolingo",
            "pdf_url": "https://example.com/document.pdf",
            "version": "v2"
        }
        
        response = client.post(
            "/api/documents",
            data=data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "test-doc-789"

    def test_upload_document_invalid_url(self):
        """Test document upload with invalid URL."""
        data = {
            "company_id": "duolingo",
            "pdf_url": "not-a-valid-url"
        }
        
        response = client.post(
            "/api/documents",
            data=data
        )
        
        assert response.status_code == 400
        assert "URL" in response.json()["detail"]

    @patch("backend.api.routes.documents.pdf_service")
    @patch("backend.api.routes.documents._upload_pdf_to_imagekit")
    def test_upload_document_corrupted_pdf(
        self,
        mock_upload_imagekit,
        mock_pdf_service
    ):
        """Test document upload with corrupted PDF."""
        # Mock PDF processing to fail
        mock_pdf_service.process_pdf_from_bytes.side_effect = ValueError("Invalid PDF")
        
        pdf_content = b"Not a valid PDF"
        files = {
            "pdf_file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")
        }
        data = {"company_id": "duolingo"}
        
        response = client.post(
            "/api/documents",
            files=files,
            data=data
        )
        
        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"] or "corrupted" in response.json()["detail"].lower()
        
        # ImageKit upload should not be called if PDF is invalid
        mock_upload_imagekit.assert_not_called()
