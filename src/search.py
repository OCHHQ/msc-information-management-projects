#src/sreach.py

def keyword_search(content: str, keyword: str) -> list:
    """
    search for keyword in the text content.
    Return a list of line where the keyword appear.

    notic: This is Msc project 
    """

    lines = content.split('\n')
    matches = [line.strip() for line in lines if keyword.lower() in line.lower()]
    return matches
    
