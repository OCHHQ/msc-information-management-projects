import re

def find_keyword_sentences(text, keyword):
    """
    Return list of sentences that contain the keyword with highlighting.
    """
    # Normalize keyword
    key_norm = re.sub(r"\s+", " ", keyword.strip().lower())
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    matches = []
    for sentence in sentences:
        s_clean = re.sub(r"\s+", " ", sentence.strip())
        s_norm = s_clean.lower()
        
        if key_norm in s_norm:
            # Highlight the keyword in the sentence
            highlighted = re.sub(
                f"({re.escape(key_norm)})", 
                "**\\1**",  # Wrap in double asterisks
                s_clean, 
                flags=re.IGNORECASE
            )
            matches.append(highlighted)
    
    return matches

def rank_results(matches, keyword):
    """
    Rank matches by relevance score.
    """
    keyword_lower = keyword.lower()
    scored_matches = []

    for match in matches:
        score = 0

        # Higher score for exact case match
        if keyword in match:
            score += 3
        elif keyword_lower in match.lower():
            score += 2

        # Higher score for multiple occurrences
        occurrences = match.lower().count(keyword_lower)
        score += occurrences * 1.5

        # Higher score for shorter sentences (more focused)
        score += max(0, 10 - len(match.split()) / 5)

        scored_matches.append((score, match))

    # Sort by score descending
    scored_matches.sort(key=lambda x: x[0], reverse=True)

    # Return just the sorted matches
    return [match for score, match in scored_matches]

def display_results(matches, filename, page_size=5):
    """
    Display results with pagination.
    """
    if not matches:
        print(f"No matches found in {filename}.")
        return

    print(f"Found {len(matches)} matches in {filename}:\n")

    # Paginate results
    for page_num in range(0, len(matches), page_size):
        page_matches = matches[page_num:page_num + page_size]

        for i, match in enumerate(page_matches, page_num + 1):
            print(f"{i}. {match}")

        # Ask to continue if there are more results
        if page_num + page_size < len(matches):
            input("\nPress Enter for more results...")
            print()

def boolean_search(text, query):
    """
    Support AND, OR, NOT operators.
    Example: "computer AND hardware", "software OR program", "system NOT network"
    """
    query = query.upper()
    
    if " AND " in query:
        terms = [term.strip().lower() for term in query.split(" AND ")]
        return all(term in text.lower() for term in terms)
    
    elif " OR " in query:
        terms = [term.strip().lower() for term in query.split(" OR ")]
        return any(term in text.lower() for term in terms)
    
    elif " NOT " in query:
        terms = query.split(" NOT ")
        include = terms[0].strip().lower()
        exclude = terms[1].strip().lower()
        return include in text.lower() and exclude not in text.lower()
    
    else:
        # Regular search
        return query.lower() in text.lower()

"""
REPLACE your advanced_search function in src/search_engine.py with this:
"""

def advanced_search(text, query):
    """
    Handle different search types: phrase search, boolean search, or simple search.
    
    Args:
        text (str): The text to search in
        query (str): The search query
    
    Returns:
        list: Matching sentences
    """
    # 1. CHECK FOR PHRASE SEARCH FIRST (quotes)
    if '"' in query:
        return phrase_search(text, query)
    
    # 2. CHECK FOR BOOLEAN SEARCH (AND, OR, NOT)
    elif any(op in query.upper() for op in [' AND ', ' OR ', ' NOT ']):
        # Boolean search logic
        sentences = re.split(r'(?<=[.!?])\s+', text)
        matches = []
        
        for sentence in sentences:
            s_clean = re.sub(r"\s+", " ", sentence.strip())
            
            if boolean_search(s_clean, query):
                # Highlight all terms in the query
                highlighted = s_clean
                for term in extract_terms(query):
                    highlighted = re.sub(
                        f"({re.escape(term)})",
                        "**\\1**",
                        highlighted,
                        flags=re.IGNORECASE
                    )
                matches.append(highlighted)
        
        return matches
    
    # 3. SIMPLE SEARCH (no quotes, no operators)
    else:
        return find_keyword_sentences(text, query)


def extract_terms(query):
    """
    Extract search terms from boolean query.
    """
    # Remove operators and split
    terms = re.split(r'\s+(?:AND|OR|NOT)\s+', query, flags=re.IGNORECASE)
    return [term.strip().lower() for term in terms if term.strip()]


"""
EXACT FIX for src/search_engine.py

FIND THIS in your file:
----------------------------
def phrase_search(text, phrase):
    phrase = phrase.strip('"').lower()
    text_lower = text.lower()
    return phrase in text_lower


REPLACE IT WITH THIS:
----------------------------
"""

def phrase_search(text, phrase):
    """
    Search for exact phrases and return matching sentences.
    
    Args:
        text (str): The text to search in
        phrase (str): The phrase to search for (with or without quotes)
    
    Returns:
        list: Sentences containing the exact phrase
    """
    import re
    
    # Remove quotes and normalize
    phrase = phrase.strip('"').lower()
    
    if not phrase:
        return []
    
    # Split text into sentences using multiple delimiters
    sentences = re.split(r'[.!?\n\r]+', text)
    
    matching_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        
        # Skip very short fragments
        if len(sentence) < 10:
            continue
        
        # Case-insensitive search for the phrase
        if phrase in sentence.lower():
            # Normalize whitespace
            clean_sentence = ' '.join(sentence.split())
            
            # Avoid duplicates
            if clean_sentence and clean_sentence not in matching_sentences:
                matching_sentences.append(clean_sentence)
    
    return matching_sentences
    

def handle_quoted_phrases(query):
    """
    Handle quoted phrases in search queries.
    """
    # Find quoted phrases
    phrases = re.findall(r'"([^"]+)"', query)
    
    # Remove quotes from original query for term extraction
    simple_query = re.sub(r'"[^"]+"', '', query)
    
    return phrases, simple_query.strip()


