from flask import Flask, render_template,request, jsonify, send_file ,flash, redirect, url_for
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
import uuid
import io


#my existing modules
import sys
sys.path.append('./src')
from extractor import extract_text_from_pdf
from search_engine import find_keyword_sentences, rank_results, advanced_search

app = Flask(__name__)
app.secert_key = "your-secret-key" 

#configuration
UPLOAD_FOLDER = 'data'
EXPORT_FOLDER = 'exports'
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 16 * 1024 * 1024

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

def allowed_file(filename):
    """ file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def working_phrase_search(text, query):
    """ my previous advance search which orginally fix conatian bugs, so i had use this working phrase as alt to ADVANCE_SEARCH"""
    import re

    if '"' not in query:
        return[]
    
    phrase_matches = re.findall(r'"([^"]*)"', query)
    if not phrase_matches:
        return[]

    all_matches =[]

    for phrase in phrase_matches:
        phrase = phrase.strip()
        if not phrase:
            continue
        
        sentences = re.split(r'[.!?\n\r]+', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue

            if phrase.lower() in sentence.lower():
                clean_sentence = ' '.join(sentence.split())
                if clean_sentence and  clean_sentence not in all_matches:
                    all_matches.append(clean_sentence)

    return all_matches



"""
Replace the search_across_pdfs function in app.py with this version
that uses YOUR working search functions
"""

def search_across_pdfs(query):
    """Main search function that processes all PDFs using YOUR working functions"""
    results = {
        'query': query,
        'total_matches': 0,
        'files_searched': 0,
        'files_with_matches': 0,
        'search_time': 0,
        'matches_by_file': {}
    }
    
    start_time = datetime.now()
    
    # Get all PDF files
    pdf_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith('.pdf')]
    results['files_searched'] = len(pdf_files)
    
    if not pdf_files:
        results['error'] = 'No PDF files found in data folder'
        return results
    
    # Search each PDF
    for pdf_file in pdf_files:
        pdf_path = os.path.join(UPLOAD_FOLDER, pdf_file)
        
        try:
            # Extract text
            text = extract_text_from_pdf(pdf_path)
            
            # Use YOUR working advanced_search function!
            matches = advanced_search(text, query)
            
            # Determine search type for display
            if '"' in query:
                search_type = 'phrase'
            elif any(op in query.upper() for op in [' AND ', ' OR ', ' NOT ']):
                search_type = 'boolean'
            else:
                search_type = 'simple'
            
            # Process results
            if matches:
                # Rank and deduplicate
                try:
                    matches = rank_results(matches, query)
                    matches = list(dict.fromkeys(matches))
                except:
                    pass  # If ranking fails, keep original matches
                
                results['matches_by_file'][pdf_file] = {
                    'matches': matches,
                    'count': len(matches),
                    'search_type': search_type
                }
                
                results['total_matches'] += len(matches)
                results['files_with_matches'] += 1
                
        except Exception as e:
            results['matches_by_file'][pdf_file] = {
                'error': str(e),
                'count': 0,
                'search_type': 'error'
            }
    
    # Calculate search time
    end_time = datetime.now()
    results['search_time'] = (end_time - start_time).total_seconds()
    
    return results



@app.route('/')
def index():
    """main search page"""

    pdf_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith('.pdf')]
    return render_template('index.html', pdf_files=pdf_files)

@app.route('/search', methods=['POST'])
def search():
    """ Here currently handles my search requests"""
    query = request.form.get('query', '').strip()

    if not query:
        flash('please enter a search query', 'error')
        return redirect(url_for('index'))

    results = search_across_pdfs(query)

    return render_template('results.html', results=results)

@app.route('/export/<format>', methods=['POST'])
def export_results(format):
    """Export search results to different formats"""
    from datetime import datetime
    
    try:
        data = request.get_json()
        query = data.get('query', 'Unknown Query')
        results = data.get('results', [])
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'txt':
            # Text export
            output = io.StringIO()
            output.write(f"IR LEGAL SEARCH RESULTS\n")
            output.write(f"{'='*70}\n")
            output.write(f"Query: {query}\n")
            output.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            output.write(f"Total Results: {len(results)}\n")
            output.write(f"{'='*70}\n\n")
            
            for i, result in enumerate(results, 1):
                output.write(f"Result {i}:\n")
                output.write(f"{result['text']}\n")
                output.write(f"Source: {result['filename']}\n")
                output.write(f"{'-'*70}\n\n")
            
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                mimetype='text/plain',
                as_attachment=True,
                download_name=f'search_results_{timestamp}.txt'
            )
        
        elif format == 'csv':
            # CSV export
            output = io.StringIO()
            output.write('Index,Filename,Match Text\n')
            
            for i, result in enumerate(results, 1):
                text = result['text'].replace('"', '""')  # Escape quotes
                filename = result['filename'].replace('"', '""')
                output.write(f'{i},"{filename}","{text}"\n')
            
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'search_results_{timestamp}.csv'
            )
        
        elif format == 'html':
            # HTML export
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Search Results - {query}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #0d6efd; color: white; padding: 20px; border-radius: 8px; }}
        .result {{ background: white; padding: 15px; margin: 15px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .result-header {{ color: #0d6efd; font-weight: bold; margin-bottom: 10px; }}
        .filename {{ color: #666; font-size: 0.9em; margin-top: 10px; }}
        .highlight {{ background-color: #ffeb3b; padding: 2px 4px; border-radius: 3px; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>IR Legal Search Results</h1>
        <p><strong>Query:</strong> {query}</p>
        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Total Results:</strong> {len(results)}</p>
    </div>
"""
            
            for i, result in enumerate(results, 1):
                text = result['text'].replace('<', '&lt;').replace('>', '&gt;')
                html += f"""
    <div class="result">
        <div class="result-header">Result {i}</div>
        <div>{text}</div>
        <div class="filename">Source: {result['filename']}</div>
    </div>
"""
            
            html += """
</body>
</html>
"""
            
            return send_file(
                io.BytesIO(html.encode('utf-8')),
                mimetype='text/html',
                as_attachment=True,
                download_name=f'search_results_{timestamp}.html'
            )
        
        else:
            return jsonify({'error': 'Invalid format'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/search', methods=['POST'])
def api_search():
    """MY API SEARCH ENDPOINT FOR (for AJAX requests)"""
    data = request.get_json()
    query = data.get('query', '').strip()

    if not query:
        return jsonify({'error': 'QUERY IS REQUIRED '}), 400

    results = search_across_pdfs(query)
    return jsonify(results)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """hANDle file uploads"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)


            #Ensuring unique filename
            if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"

            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash(f'file {filename} uploaded successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Only PDF file are allowed', 'error')

    return render_template('upload.html')





@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/help')
def help():
    """Help page with search syntax"""
    return render_template('help.html')

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error='page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error='Internal server error'), 500

if __name__ == '__main__':
    #required dir exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(EXPORT_FOLDER, exist_ok=True)

    app.run(debug=True, host='0.0.0.0', port=5000)




