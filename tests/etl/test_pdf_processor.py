from pathlib import Path

import pytest

from backend.etl.pdf_processor import process_pdf


def test_pdf_processor_hybrid_on_duolingo_pdf():
    pdf_path = Path("docs/Q3FY25 Duolingo 9-30-25 Shareholder Letter Final.pdf")
    if not pdf_path.exists():
        pytest.skip("Duolingo PDF not found.")

    result = process_pdf(str(pdf_path))
    assert result["engine"] == "hybrid"
    assert result["pages"]
