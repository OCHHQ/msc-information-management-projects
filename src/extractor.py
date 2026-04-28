#src/document.py
# This module provides functionality to extract text from a PDF file.
import os

import PyPDF2
import pdfplumber
import fitz


def _normalize_text(chunks):
    return "\n".join(chunk.strip() for chunk in chunks if chunk and chunk.strip())


def _extract_with_pypdf2(pdf_path, max_pages=None):
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        pages = reader.pages[:max_pages] if max_pages else reader.pages
        return _normalize_text(page.extract_text() or "" for page in pages)


def _extract_with_pdfplumber(pdf_path, max_pages=None):
    with pdfplumber.open(pdf_path) as pdf:
        pages = pdf.pages[:max_pages] if max_pages else pdf.pages
        return _normalize_text(page.extract_text() or "" for page in pages)


def _extract_with_pymupdf(pdf_path, max_pages=None):
    document = fitz.open(pdf_path)
    try:
        page_total = min(len(document), max_pages) if max_pages else len(document)
        return _normalize_text(document.load_page(index).get_text("text") for index in range(page_total))
    finally:
        document.close()


def extract_text_from_pdf(pdf_path, max_pages=None):
    """
    Extract text from a PDF file.
    DIKW: This is the 'Data - information' stage - raw PDF - readable text.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"The file {pdf_path} does not exist.")

    errors = []
    extractors = (
        ("PyPDF2", _extract_with_pypdf2),
        ("pdfplumber", _extract_with_pdfplumber),
        ("PyMuPDF", _extract_with_pymupdf),
    )

    for name, extractor in extractors:
        try:
            # Different hosts can behave differently with PDF parsers, so we try a few in order.
            text = extractor(pdf_path, max_pages=max_pages)
            if text.strip():
                return text
            errors.append(f"{name}: extracted empty text")
        except Exception as exc:
            errors.append(f"{name}: {exc}")

    error_summary = "; ".join(errors[:3]) or "no extractor attempted"
    raise RuntimeError(f"Unable to extract text from {os.path.basename(pdf_path)}. {error_summary}")
