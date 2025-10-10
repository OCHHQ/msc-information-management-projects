# IR Legal Search Tool

A powerful web-based document search application designed for legal research and information retrieval.

## Features

- **Phrase Search**: Search for exact phrases using quotation marks
- **Boolean Search**: Use AND, OR, NOT operators for complex queries  
- **Simple Search**: Basic keyword searching
- **Web Interface**: User-friendly web application
- **PDF Processing**: Extract and search text from PDF documents
- **Result Export**: Export search results in multiple formats
- **Intelligent Ranking**: Results ranked by relevance

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python app.py
   ```

3. **Open in Browser**:
   Navigate to `http://localhost:5000`

### Search Types

- **Phrase Search**: `"contract law"`
- **Boolean Search**: `contract AND liability`
- **Simple Search**: `contract`

### Uploading Documents

1. Click "Upload" in the navigation
2. Drag and drop PDF files or click to browse
3. Files are processed and added to your searchable library

## Project Structure

```
ir_legal_search_tool/
├── app.py              # Flask web application
├── data/               # PDF document storage
├── src/                # Core search modules
├── templates/          # HTML templates
├── static/             # CSS, JS, images
├── exports/            # Search result exports
└── requirements.txt    # Python dependencies
```

## Development

This tool was developed as part of an MSc Information Management project, demonstrating advanced information retrieval techniques and web application development.

## License
Academic project - all rights reserved.
