#src/test_document.py
import os

from document import extract_test_from_pdf

pdf_path = "../data/sample1.pdf"

print(f"Current working directory: {os.getcwd()}")
print(f"PDF path: {os.path.abspath(pdf_path)}")
print(f"File exists: {os.path.exists(pdf_path)}")

try:
    content = extract_test_from_pdf(pdf_path)
    print("Extracted content:\n", content[:100])  # Print first 1000 characters for brevity
except Exception as e:
    print(f"Error occur: {e}") # Print the error message