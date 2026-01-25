"""
Tests for Text Normalizer.
"""

import pytest

from backend.etl.normalizer import normalize_text, normalize_date, normalize_number


class TestNormalizer:
    """Test text normalizer functionality."""

    def test_normalize_text_empty(self):
        """Test normalizing empty text."""
        result = normalize_text("")
        assert result == ""

    def test_normalize_text_whitespace(self):
        """Test normalizing excessive whitespace."""
        text = "This   has    multiple    spaces"
        result = normalize_text(text)
        assert "  " not in result  # No double spaces

    def test_normalize_text_newlines(self):
        """Test normalizing excessive newlines."""
        text = "Line 1\n\n\n\nLine 2"
        result = normalize_text(text)
        assert "\n\n\n" not in result  # Max 2 consecutive newlines

    def test_normalize_text_strip(self):
        """Test stripping leading/trailing whitespace."""
        text = "   Text with spaces   "
        result = normalize_text(text)
        assert result == "Text with spaces"

    def test_normalize_text_preserves_single_newlines(self):
        """Test that single newlines are preserved."""
        text = "Paragraph 1\n\nParagraph 2"
        result = normalize_text(text)
        assert "\n\n" in result  # Paragraph breaks preserved

    def test_normalize_text_complex(self):
        """Test normalizing complex text."""
        text = "   This   is   a   test   \n\n\n\n   with   multiple   \n\n   issues   "
        result = normalize_text(text)
        assert result.startswith("This")
        assert result.endswith("issues")
        assert "  " not in result
        assert "\n\n\n" not in result

    def test_normalize_number_placeholder(self):
        """Test number normalizer (placeholder)."""
        text = "Revenue: $100,000"
        result = normalize_number(text)
        # Currently just returns as-is
        assert result == text

    def test_normalize_date_placeholder(self):
        """Test date normalizer (placeholder)."""
        text = "Date: 01/25/2026"
        result = normalize_date(text)
        # Currently just returns as-is
        assert result == text
