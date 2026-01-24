from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import fitz


def _page_to_bgr(page: fitz.Page) -> "numpy.ndarray":
    from PIL import Image
    import numpy as np

    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    mode = "RGB" if pix.alpha == 0 else "RGBA"
    image = Image.frombytes(mode, (pix.width, pix.height), pix.samples).convert("RGB")
    rgb = np.array(image)
    return rgb[:, :, ::-1]


def _extract_text(doc: fitz.Document) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        pages.append(
            {"page": page_index + 1, "text": page.get_text("text"), "source": "text"}
        )
    return pages


def _extract_ocr(doc: fitz.Document) -> list[dict[str, Any]]:
    try:
        from rapidocr_onnxruntime import RapidOCR
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(f"RapidOCR unavailable: {exc}") from exc

    ocr = RapidOCR()
    pages: list[dict[str, Any]] = []
    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        image = _page_to_bgr(page)
        result, _ = ocr(image)
        text_lines = []
        for line in result or []:
            text_lines.append(line[1])
        pages.append(
            {"page": page_index + 1, "text": "\n".join(text_lines), "source": "ocr"}
        )
    return pages


def _extract_hybrid(doc: fitz.Document, threshold: int) -> list[dict[str, Any]]:
    try:
        from rapidocr_onnxruntime import RapidOCR
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(f"RapidOCR unavailable: {exc}") from exc

    ocr = RapidOCR()
    pages: list[dict[str, Any]] = []
    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        text = page.get_text("text")
        if len(text.strip()) >= threshold:
            pages.append({"page": page_index + 1, "text": text, "source": "text"})
            continue
        image = _page_to_bgr(page)
        result, _ = ocr(image)
        text_lines = []
        for line in result or []:
            text_lines.append(line[1])
        pages.append(
            {"page": page_index + 1, "text": "\n".join(text_lines), "source": "ocr"}
        )
    return pages


def process_pdf(source: str, use_ocr: bool | None = None) -> dict[str, Any]:
    pdf_path = Path(source)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pdf_bytes = pdf_path.read_bytes()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    if use_ocr is None:
        threshold = int(os.getenv("PDF_OCR_TEXT_THRESHOLD", "120"))
        pages = _extract_hybrid(doc, threshold)
        return {"engine": "hybrid", "pages": pages}

    if use_ocr:
        pages = _extract_ocr(doc)
        return {"engine": "paddleocr", "pages": pages}

    pages = _extract_text(doc)
    return {"engine": "pymupdf", "pages": pages}
