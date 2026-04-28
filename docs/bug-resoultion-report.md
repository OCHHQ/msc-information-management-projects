#Bug resoultion report: phrase search functionality 

Fix a cirtical bug in the phrase search functionality when testing at 2pm , 2/10/2025
that prevent quoted phrase searches from returning results despite the phrases existing in the documents.

## problem statement

### Initial symptoms

1. Search query: "information system"
2. Expected: return sentences containing the exact phrase
3. Actual: empty result (0 matches)
4. impact : was that the phrase search non-functional 

### Diagnostic Process

#### phase 1: compoent isolation
Tested each function individually: 
- PDF text extration: working (175, 362 characters extracted)
- Phrase exists in text: confirmed (120 occurances)
- Boolean search : working correctly 
- X phrase search: returning empty list 


#### Phase 2" root cause Analysis
phython
# Broken code (orginal)
def phrase_search(text, phrase):
    phrase = phrase.strip('"').lower()
    text_lower = text.lower
    return phrase in text_lower #results True/False, not results!

#### phase 3: Secondary issue

def advanced_search(text, query):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    for sentence in sentences:
        if boolean_search(s_clean, query):
         #This Never check the phrase search

# problem was advanced_search never routed to phrase_search function

## solution implemented 
Fix 1: 

def phrase_search(text, phrase):
    """ here we search for the exact phrases and return the matching """
    import re

    phrase = phrase.strip('"').lower()
        if not phrase:
            return []

sentences = re.split(r'[.!?z\n\r]+', text)
matching_sentences = []

for sentence in sentences:
    sentence = sentences.strip()
    if len(sentence) < 10:
        continue

    if phrase in sentence.lower():
        clean_sentence = ' '.join(sentence.split())
        if clean_sentence and clean_sentence not in matching_sentences:
            matching_sentence.append(clean_sentence)

return matching_sentences


## Fix 2: Corrected advanced_search Routing

def advanced_search(text, query):
    """Route to appropriate search function based on query type."""
    
    # Check for phrase search first
    if '"' in query:
        return phrase_search(text, query)
    
    # Check for boolean operators
    elif any(op in query.upper() for op in [' AND ', ' OR ', ' NOT ']):
        # Boolean search logic...
        return boolean_results
    
    # Default to simple search
    else:
        return find_keyword_sentences(text, query)


## Lessons Learned

Test individual components: Isolated testing revealed the exact breaking point
Check return types: Mismatched return types (bool vs list) cause silent failures
Verify routing logic: Even working functions fail if never called
Use diagnostics first: Systematic testing saves time over random fixes

## Testing Methodology
Created diagnostic script that tests:

PDF extraction
Text content verification
Each search function independently
Integration between functions
Edge cases and error handling

Date
October 2025
Developer
Collins Enoseje
MSc Information Management
Ahmadu Bello University
EOF

## Step 3: Setup Guide
```bash
cat > docs/setup-guide.md << 'EOF'
# IR Legal Search Tool - Setup Guide

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (optional, for version control)

## Installation

### 1. Clone or Download Project
```bash
cd ~/msc-information-management-projects
# If using git:
git clone <repository-url> ir_legal_search_tool
# Or download and extract ZIP file

2. Install Dependencies

cd ir_legal_search_tool
pip install -r requirements.txt

Required packages:

Flask==3.0.0
PyPDF2==3.0.1
pdfplumber==0.10.0
pymupdf==1.23.26
nltk==3.8.1
Other dependencies listed in requirements.txt


3. Verify Project Structure

ir_legal_search_tool/
├── app.py                  # Flask web application
├── data/                   # PDF storage
├── src/                    # Core modules
│   ├── extractor.py       # PDF text extraction
│   ├── search_engine.py   # Search algorithms
│   └── main.py            # CLI interface
├── templates/             # HTML templates
├── static/                # CSS, JS, images
├── docs/                  # Documentation
└── requirements.txt       # Dependencies

4. Add PDF Documents

# Copy your PDF files to the data directory
cp /path/to/your/pdfs/*.pdf data/
you can still upload via the web interface 

Running the Application
Web Interface (Recommended)

python app.py

Then open browser to: http://localhost:5000

## Command Line Interface
bash

cd src
python main.py

## Command Line Interface
cd src
python main.py

### Troubleshooting
Import Errors
If you get import errors, ensure you're in the project root:

cd ~/msc-information-management-projects/ir_legal_search_tool
python app.py

Template Not Found
Verify templates directory exists and contains all HTML files:

ls templates/
# Should show: base.html, index.html, results.html, etc.

No PDF Files Found
Ensure PDFs are in the data directory:

ls data/*.pdf

Port Already in Use
If port 5000 is busy, change it in app.py:

app.run(debug=True, port=5001)  # Use different port

Development Mode
For development with auto-reload:

export FLASK_ENV=development
python app.py

Production Deployment
For production, use a production server:

pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

Configuration
Edit config/config.py to customize:

Upload folder location
File size limits
Secret key
Debug mode

Support
For issues or questions:

Check the troubleshooting section
Review the user manual
Contact: enosejec@gmail.com

Version
1.0.0 - October 2025
EOF

## Step 4: User Manual
```bash
cat > docs/user-manual.md << 'EOF'
# IR Legal Search Tool - User Manual

## Overview

The IR Legal Search Tool is a web-based application for searching legal documents using advanced information retrieval techniques.

## Getting Started

1. Open your web browser
2. Navigate to http://localhost:5000
3. You'll see the main search interface

## Search Features

### 1. Phrase Search (Exact Matching)

Use quotation marks to search for exact phrases.

**Example:**

"information system"

**Use When:**
- Looking for specific legal terms
- Need exact wording
- Searching for quotes or definitions

**Results:** Sentences containing the exact phrase in order

### 2. Boolean Search (AND/OR/NOT)

Combine terms using boolean operators.

**Examples:**

contract AND liability
data OR information
system NOT network

**Operators:**
- **AND**: Documents must contain both terms
- **OR**: Documents can contain either term
- **NOT**: Exclude documents with the term

**Use When:**
- Need documents covering multiple topics
- Want to broaden or narrow search
- Excluding unwanted content

### 3. Simple Keyword Search

Just type words without quotes or operators.

**Example:**

contract

**Use When:**
- Exploring a topic
- Not sure of exact phrasing
- Want all mentions of a term

## Search Tips

### Do's
Use quotes for exact phrases
Combine AND for precise results
Try different synonyms
Use lowercase for consistent results
Check spelling before searching

### Don'ts
❌ Don't use too many operators
❌ Don't search very common words alone
❌ Don't forget quotes for phrases
❌ Don't use special characters unnecessarily

## Understanding Results

### Result Display
- **Match count**: Number of results found
- **File name**: Which document contains the match
- **Context**: Sentence or paragraph with the match
- **Highlighting**: Search terms highlighted in yellow

### Result Actions
- **Copy**: Copy result text to clipboard
- **Highlight**: Toggle highlight on/off
- **Export**: Save results to file

## Uploading Documents

1. Click "Upload" in navigation
2. Click "Choose File" or drag-and-drop
3. Select a PDF file
4. Click "Upload"
5. Document becomes searchable immediately

### Upload Requirements
- Only PDF files accepted
- Maximum 16MB per file
- Text-based PDFs work best
- Scanned PDFs may have limited searchability

## Exporting Results

1. Perform a search
2. Click "Export" button
3. Choose format:
   - **Text**: Plain text file
   - **CSV**: Spreadsheet format
   - **HTML**: Formatted report

## Keyboard Shortcuts

- `Ctrl + /`: Focus search box
- `Ctrl + Enter`: Submit search
- `Esc`: Clear search box

## Best Practices

### For Legal Research
1. Start with phrase searches for specific terms
2. Use boolean AND to find relevant documents
3. Export important results for reference
4. Review context around matches

### For Efficient Searching
1. Use specific terms over general ones
2. Combine search types as needed
3. Review first few results before refining
4. Save successful queries for reuse

## Troubleshooting

### No Results Found
- Check spelling
- Try broader terms
- Remove quotes to search individual words
- Verify documents contain your search terms

### Too Many Results
- Use phrase search with quotes
- Add AND operator to narrow scope
- Use NOT to exclude unwanted terms

### Slow Search
- Reduce number of documents
- Use more specific search terms
- Avoid searching very common words

## FAQ

**Q: Can I search multiple PDFs at once?**
A: Yes, search automatically covers all PDFs in the library.

**Q: Are searches case-sensitive?**
A: No, searches are case-insensitive.

**Q: Can I search scanned PDFs?**
A: Limited. OCR-processed PDFs work; image-only PDFs don't.

**Q: How do I delete uploaded files?**
A: Currently requires manual deletion from data folder.

## Support

Need help? Contact: enosejec@gmail.com

## Version
1.0.0 - October 2025
EOF

Step 5: Create README.md for GitHub

cat > README.md << 'EOF'
# IR Legal Search Tool

Advanced information retrieval system for legal document search and analysis.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0-green.svg)
![License](https://img.shields.io/badge/license-Academic-orange.svg)

## Features

- **Phrase Search**: Exact phrase matching with quotation marks
- **Boolean Search**: AND/OR/NOT operators for complex queries
- **Simple Search**: Basic keyword searching
- **Web Interface**: User-friendly web application
- **PDF Processing**: Automatic text extraction from PDF documents
- **Result Export**: Save results in multiple formats
- **Intelligent Ranking**: TF-IDF based relevance scoring

## Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python app.py

# Open browser
http://localhost:5000

Documentation

Setup Guide
User Manual
Bug Resolution Report

Technology Stack

Backend: Python, Flask
Frontend: HTML5, Bootstrap 5, JavaScript
PDF Processing: PyPDF2, pdfplumber
Text Processing: NLTK, Regular Expressions

### Project Structure

ir_legal_search_tool/
├── app.py              # Web application
├── data/               # PDF storage
├── src/                # Core modules
├── templates/          # HTML templates
├── static/             # CSS, JS, images
└── docs/               # Documentation

Search Examples

# Phrase search
"information system"

# Boolean search
contract AND liability
data OR information
system NOT network

# Simple search
contract

Academic Context

Course: Information Retrieval Systems
Program: MSc Information Management
Institution: Ahmadu Bello University
Year: 2024/2025

Developer
Collins Enoseje
Backend Developer | MSc Information Management

Email: enosejec@gmail.com
LinkedIn: linkedin.com/in/collinsenoseje
GitHub: github.com/OCHHQ

License
Academic Project © 2025
EOF

## Step 6: Verify Documentation
```bash
# Check all files were created
ls -la docs/
cat README.md

# View the documentation
less docs/setup-guide.md