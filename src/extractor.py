#src/document.py
# This module provides functionality to extract text from a PDF file.
# It uses the PyPDF2 library to read the PDF and extract text from each page.
import os
import PyPDF2

def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file.
    DIKW: This is the 'Data - information' stage - raw PDF - readbale text.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"The file {pdf_path} does not exist.")
    
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
    return text
