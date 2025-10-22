"""
This module provides a function to analyze a string and return a dictionary of its properties.
"""

import hashlib
from collections import Counter
from typing import Dict, Any


def analyse_string(value: str) -> Dict[str, Any]:
    """
    Computes and returns all required properties for a given string.

    Args:
        value: The string to analyze.

    Returns:
        A dictionary containing the following properties of the string:
        - length: The number of characters in the string.
        - is_palindrome: A boolean indicating whether the string is a palindrome.
        - unique_characters: The number of unique characters in the string.
        - word_count: The number of words in the string.
        - sha256_hash: The SHA256 hash of the string.
        - character_frequency_map: A dictionary mapping each character to its frequency.
    """
    sha256_hash = hashlib.sha256(value.encode("utf-8")).hexdigest()
    length = len(value)
    normalised_value = "".join(filter(str.isalnum, value)).lower()
    is_palindrome = normalised_value == normalised_value[::-1]
    unique_characters = len(set(value))
    word_count = len(value.split())
    character_frequency_map = dict(Counter(value))

    return {
        "length": length,
        "is_palindrome": is_palindrome,
        "unique_characters": unique_characters,
        "word_count": word_count,
        "sha256_hash": sha256_hash,
        "character_frequency_map": character_frequency_map,
    }
