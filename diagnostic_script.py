#!/usr/bin/env python3
"""
Core Search Engine Diagnostic Script
This script tests EVERY function in your search_engine.py to identify what's broken
"""

import sys
import os
sys.path.append('./src')

from extractor import extract_text_from_pdf
from search_engine import *

def test_basic_functionality():
    """Test 1: Can we extract PDF text?"""
    print("="*60)
    print("TEST 1: PDF TEXT EXTRACTION")
    print("="*60)
    
    try:
        pdf_path = './data/LIBS 880 -Info Sys Analysis & Design.pdf'
        text = extract_text_from_pdf(pdf_path)
        print(f"✅ PDF extraction works: {len(text)} characters extracted")
        print(f"Sample: {text[:200]}")
        return text
    except Exception as e:
        print(f"❌ PDF extraction FAILED: {e}")
        return None

def test_phrase_in_text(text):
    """Test 2: Does the phrase actually exist?"""
    print("\n" + "="*60)
    print("TEST 2: PHRASE EXISTENCE CHECK")
    print("="*60)
    
    test_phrases = [
        "information system",
        "data processing",
        "legal framework",
        "contract law"
    ]
    
    for phrase in test_phrases:
        exists = phrase.lower() in text.lower()
        count = text.lower().count(phrase.lower())
        status = "✅" if exists else "❌"
        print(f"{status} '{phrase}': {'EXISTS' if exists else 'NOT FOUND'} (count: {count})")

def test_advanced_search_function(text):
    """Test 3: Test your advanced_search function"""
    print("\n" + "="*60)
    print("TEST 3: ADVANCED_SEARCH FUNCTION")
    print("="*60)
    
    test_cases = [
        ('"information system"', 'phrase'),
        ('computer AND hardware', 'boolean'),
        ('data OR information', 'boolean'),
        ('system NOT network', 'boolean'),
    ]
    
    for query, search_type in test_cases:
        print(f"\nTesting: {query} ({search_type})")
        try:
            result = advanced_search(text, query)
            print(f"  Return type: {type(result)}")
            print(f"  Return value: {result if not isinstance(result, list) else f'list with {len(result)} items'}")
            
            if isinstance(result, list):
                if len(result) > 0:
                    print(f"  ✅ Found {len(result)} matches")
                    print(f"  First match: {result[0][:100]}...")
                else:
                    print(f"  ❌ No matches found (empty list)")
            elif isinstance(result, bool):
                print(f"  ⚠️  Returns boolean: {result} (should return list of matches)")
        except Exception as e:
            print(f"  ❌ ERROR: {e}")

def test_find_keyword_sentences(text):
    """Test 4: Test find_keyword_sentences function"""
    print("\n" + "="*60)
    print("TEST 4: FIND_KEYWORD_SENTENCES FUNCTION")
    print("="*60)
    
    test_keywords = [
        'information',
        'system',
        'data',
        'contract'
    ]
    
    for keyword in test_keywords:
        print(f"\nTesting keyword: '{keyword}'")
        try:
            result = find_keyword_sentences(text, keyword)
            print(f"  Return type: {type(result)}")
            if isinstance(result, list):
                print(f"  ✅ Found {len(result)} matches")
                if len(result) > 0:
                    print(f"  First match: {result[0][:100]}...")
            else:
                print(f"  ⚠️  Unexpected return type: {type(result)}")
        except Exception as e:
            print(f"  ❌ ERROR: {e}")

def test_handle_quoted_phrases():
    """Test 5: Test handle_quoted_phrases function"""
    print("\n" + "="*60)
    print("TEST 5: HANDLE_QUOTED_PHRASES FUNCTION")
    print("="*60)
    
    test_queries = [
        '"information system"',
        '"data processing" AND analysis',
        '"legal framework" OR "contract law"',
    ]
    
    for query in test_queries:
        print(f"\nTesting: {query}")
        try:
            phrases, remaining = handle_quoted_phrases(query)
            print(f"  ✅ Extracted phrases: {phrases}")
            print(f"  Remaining text: {remaining}")
        except Exception as e:
            print(f"  ❌ ERROR: {e}")

def test_rank_results():
    """Test 6: Test rank_results function"""
    print("\n" + "="*60)
    print("TEST 6: RANK_RESULTS FUNCTION")
    print("="*60)
    
    sample_results = [
        "This sentence contains information system twice information system.",
        "This mentions information system once.",
        "No match here.",
        "Information system appears at the start."
    ]
    
    query = "information system"
    
    print(f"Testing with {len(sample_results)} sample results")
    try:
        ranked = rank_results(sample_results, query)
        print(f"  ✅ Ranking successful")
        print(f"  Input: {len(sample_results)} items")
        print(f"  Output: {len(ranked)} items")
        print("\n  Ranked order:")
        for i, result in enumerate(ranked[:3], 1):
            print(f"    {i}. {result[:80]}...")
    except Exception as e:
        print(f"  ❌ ERROR: {e}")

def inspect_search_engine_module():
    """Test 7: Inspect what functions are available"""
    print("\n" + "="*60)
    print("TEST 7: MODULE INSPECTION")
    print("="*60)
    
    import search_engine
    
    print("Available functions in search_engine.py:")
    for name in dir(search_engine):
        if not name.startswith('_'):
            obj = getattr(search_engine, name)
            if callable(obj):
                print(f"  ✅ {name}")

def main():
    """Run all diagnostic tests"""
    print("\n" + "🔬 CORE SEARCH ENGINE DIAGNOSTIC REPORT")
    print("="*60 + "\n")
    
    # Test 1: PDF Extraction
    text = test_basic_functionality()
    if not text:
        print("\n❌ CRITICAL: Cannot extract PDF text. Fix this first!")
        return
    
    # Test 2: Phrase Existence
    test_phrase_in_text(text)
    
    # Test 3: Advanced Search
    test_advanced_search_function(text)
    
    # Test 4: Find Keyword Sentences
    test_find_keyword_sentences(text)
    
    # Test 5: Handle Quoted Phrases
    test_handle_quoted_phrases()
    
    # Test 6: Rank Results
    test_rank_results()
    
    # Test 7: Module Inspection
    inspect_search_engine_module()
    
    # Final Assessment
    print("\n" + "="*60)
    print("DIAGNOSTIC COMPLETE")
    print("="*60)
    print("\n📋 Next Steps:")
    print("1. Review the test results above")
    print("2. Identify which functions are broken")
    print("3. Fix the broken functions one by one")
    print("4. Re-run this diagnostic script")
    print("5. Only proceed to web interface when ALL tests pass ✅")
    print("\n⚠️  DO NOT build the web interface until these tests pass!")

if __name__ == "__main__":
    main()
