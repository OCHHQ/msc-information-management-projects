import os
import re
from extractor import extract_text_from_pdf
from search_engine import find_keyword_sentences, rank_results, advanced_search, handle_quoted_phrases

DATA_DIR = "../data"

def working_phrase_search(text, query):
    """
    Working phrase search function to replace buggy advanced_search for phrases
    """
    if '"' not in query:
        return []
    
    # Extract phrase from quotes
    phrase_matches = re.findall(r'"([^"]*)"', query)
    if not phrase_matches:
        return []
    
    all_matches = []
    
    for phrase in phrase_matches:
        phrase = phrase.strip()
        if not phrase:
            continue
            
        # Split text into sentences - handle multiple delimiters
        sentences = re.split(r'[.!?\n\r]+', text)
        
        # Find sentences containing the phrase (case-insensitive)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:  # Skip very short fragments
                continue
                
            if phrase.lower() in sentence.lower():
                # Clean up the sentence - normalize whitespace
                clean_sentence = ' '.join(sentence.split())
                if clean_sentence and clean_sentence not in all_matches:
                    all_matches.append(clean_sentence)
    
    return all_matches

# Update scan through multiple PDF files in the data directory
pdf_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.pdf')]

if not pdf_files:
    print("No PDF files found in data folder.")
    exit()

# Get key from Users
keyword = input("Enter a keyword to search: ").strip()

# Track over matches
total_matches = 0
files_with_matches = []

# Search PDF files
for pdf_file in pdf_files:
    pdf_path = os.path.join(DATA_DIR, pdf_file)
    print(f"\nSearching in {pdf_file}...")

    text = ""

    try:
        text = extract_text_from_pdf(pdf_path)
    except Exception as e:
        print(f"Error extracting text from {pdf_file}: {e}")
        continue

    # FIXED ADVANCED SEARCH LOGIC
    matches = []
    
    # Check for advanced search features
    if '"' in keyword:
        print("🔍 Phrase search detected")
        # Use working phrase search instead of buggy advanced_search
        matches = working_phrase_search(text, keyword)
        
    elif any(op in keyword.upper() for op in [' AND ', ' OR ', ' NOT ']):
        print("🔍 Boolean search detected")
        # Use advanced_search for boolean (assuming it works for boolean)
        matches = advanced_search(text, keyword)

    else:
        print("🔍 Simple search detected")
        # Simple search
        matches = find_keyword_sentences(text, keyword)

    # Process results
    if matches:
        # Rank results by relevance and remove duplicates
        matches = rank_results(matches, keyword)
        matches = list(dict.fromkeys(matches))
        
        # Update counters
        total_matches += len(matches)
        if pdf_file not in files_with_matches:
            files_with_matches.append(pdf_file)
        
        # Display results for this file
        print(f"✅ Found {len(matches)} matches in {pdf_file}:")
        for i, match in enumerate(matches[:5], 1):  # Show top 5 matches
            print(f"  {i}. {match[:200]}{'...' if len(match) > 200 else ''}")
        
        if len(matches) > 5:
            print(f"  ... and {len(matches) - 5} more matches")
    else:
        print(f"❌ No matches found in {pdf_file}")

# Final summary
print(f"\n" + "="*50)
print("SEARCH SUMMARY")
print("="*50)
print(f"Total matches: {total_matches}")
print(f"Files with matches: {len(files_with_matches)}")
if files_with_matches:
    print("Files containing results:")
    for file in files_with_matches:
        print(f"  - {file}")
else:
    print("No files contained the search term.")