"""
Text Normalizer for cleaning and normalizing extracted text.
"""

import re
from typing import Any


def normalize_text(text: str) -> str:
    """
    Normalize text by cleaning whitespace, formatting, etc.

    Args:
        text: Raw text to normalize

    Returns:
        Normalized text
    """
    if not text:
        return ""

    # First, normalize excessive newlines (max 2 consecutive)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Replace tabs and multiple spaces with single space (but preserve newlines)
    # Split by newlines, normalize each line, then rejoin
    lines = text.split("\n")
    normalized_lines = []
    for line in lines:
        # Normalize whitespace within each line
        normalized_line = re.sub(r"[ \t]+", " ", line.strip())
        normalized_lines.append(normalized_line)

    # Rejoin with newlines
    text = "\n".join(normalized_lines)

    # Remove leading/trailing whitespace
    text = text.strip()

    # Normalize unicode characters (optional - can be expanded)
    # text = unicodedata.normalize('NFKD', text)

    return text


def normalize_number(text: str) -> str:
    """
    Normalize number formatting in text.

    Args:
        text: Text containing numbers

    Returns:
        Text with normalized numbers
    """
    # This is a placeholder - can be expanded to normalize
    # currency, percentages, dates, etc.
    return text


def normalize_date(text: str) -> str:
    """
    Normalize date formatting in text.

    Args:
        text: Text containing dates

    Returns:
        Text with normalized dates
    """
    # This is a placeholder - can be expanded to normalize
    # various date formats to ISO format
    return text
