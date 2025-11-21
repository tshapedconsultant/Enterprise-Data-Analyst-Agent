"""
Query validation utilities.

This module provides functions to validate user queries before processing
them through the workflow, filtering out absurd or nonsensical queries.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def is_query_absurd(query: str) -> tuple[bool, Optional[str]]:
    """
    Check if a query is absurd or nonsensical.
    
    This function detects queries that:
    - Are completely unrelated to data analysis
    - Are nonsensical or gibberish
    - Are clearly not business/data questions
    - Contain only random characters or symbols
    
    Args:
        query: User query string to validate
        
    Returns:
        Tuple of (is_absurd: bool, reason: Optional[str])
        - is_absurd: True if query should be rejected
        - reason: Explanation of why query is absurd (if applicable)
    """
    if not query or not query.strip():
        return True, "Query is empty"
    
    query_lower = query.lower().strip()
    
    # Check for completely random character sequences
    # If query is mostly non-alphabetic characters, it's likely absurd
    alpha_chars = sum(1 for c in query if c.isalpha())
    total_chars = len(query.replace(" ", ""))
    if total_chars > 10 and alpha_chars / total_chars < 0.3:
        return True, "Query contains too many non-alphabetic characters"
    
    # Check for repeated single characters (e.g., "aaaaaa", "111111")
    if len(query) > 5:
        char_counts = {}
        for char in query.replace(" ", ""):
            char_counts[char] = char_counts.get(char, 0) + 1
        max_repeat = max(char_counts.values()) if char_counts else 0
        if max_repeat > len(query.replace(" ", "")) * 0.7:
            return True, "Query contains too many repeated characters"
    
    # Check for completely unrelated topics (not business/data related)
    unrelated_keywords = [
        "recipe", "cooking", "how to cook", "ingredients",
        "weather", "forecast", "temperature",
        "joke", "funny", "meme", "lol",
        "what is love", "meaning of life", "philosophy",
        "random", "test", "asdf", "qwerty",
        "hello world", "hi there", "just testing"
    ]
    
    # Only flag as absurd if query is very short AND contains unrelated keywords
    if len(query_lower.split()) <= 3:
        for keyword in unrelated_keywords:
            if keyword in query_lower:
                return True, f"Query appears to be unrelated to data analysis: '{keyword}'"
    
    # Check for gibberish (very short queries with no meaningful words)
    if len(query_lower.split()) <= 2 and len(query_lower) < 10:
        # Check if it looks like random typing
        if not any(word in query_lower for word in [
            "what", "how", "analyze", "calculate", "show", "find", "get",
            "revenue", "sales", "profit", "margin", "data", "performance",
            "trend", "growth", "quarter", "month", "year"
        ]):
            # Might be ambiguous but not necessarily absurd - let it through
            pass
    
    # Check for queries that are clearly not data analysis questions
    # (e.g., "tell me a story", "sing a song", etc.)
    absurd_patterns = [
        r"tell me (a|the) (story|joke|joke|tale)",
        r"sing (me|a|the)",
        r"what (color|animal|food) (do|does|is)",
        r"draw|paint|sketch",
        r"play (music|song|game)",
    ]
    
    for pattern in absurd_patterns:
        if re.search(pattern, query_lower):
            return True, f"Query is not a data analysis question"
    
    # Query seems reasonable
    return False, None


def is_query_too_ambiguous(query: str) -> tuple[bool, Optional[str]]:
    """
    Check if a query is too ambiguous to provide meaningful analysis.
    
    Args:
        query: User query string to check
        
    Returns:
        Tuple of (is_too_ambiguous: bool, suggestion: Optional[str])
    """
    query_lower = query.lower().strip()
    
    # Very vague queries that need more context
    vague_patterns = [
        r"^what('s| is) (our|the) (performance|status|situation)( like)?\??$",
        r"^how (are|is) (we|things|it)( doing)?\??$",
        r"^tell me (about|something) (our|the)",
    ]
    
    for pattern in vague_patterns:
        if re.match(pattern, query_lower):
            return True, "Query is too vague. Please specify what metrics or data you want analyzed (e.g., 'What are our revenue trends?' or 'Analyze profit margins')."
    
    return False, None

