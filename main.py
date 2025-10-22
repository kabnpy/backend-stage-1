"""
Main module for the String Analyzer FastAPI application.

This module defines the FastAPI application, its endpoints, and the data models used for
request and response validation.
"""

from fastapi import FastAPI, HTTPException, status, Query
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from analyser import analyse_string


class StringProperties(BaseModel):
    """
    Model for the computed properties of a string.

    Attributes:
        length: The number of characters in the string.
        is_palindrome: A boolean indicating whether the string is a palindrome.
        unique_characters: The number of unique characters in the string.
        word_count: The number of words in the string.
        sha256_hash: The SHA256 hash of the string, used as its ID.
        character_frequency_map: A dictionary mapping each character to its frequency.
    """

    length: int
    is_palindrome: bool
    unique_characters: int
    word_count: int
    sha256_hash: str = Field(..., alias="id")
    character_frequency_map: Dict[str, int]


class StringAnalyzerResult(BaseModel):
    """
    Model for the complete stored string analysis object.

    Attributes:
        id: The SHA256 hash of the string.
        value: The original string.
        properties: The computed properties of the string.
        created_at: The timestamp when the string was analyzed.
    """

    id: str
    value: str
    properties: StringProperties
    created_at: datetime


class StringInput(BaseModel):
    """
    Model for the incoming string to analyze.

    Attributes:
        value: The string to be analyzed.
    """

    value: str


# In-memory database to store the results of the string analysis.
# The key is the SHA256 hash of the string.
DATABASE: Dict[str, StringAnalyzerResult] = {}

app = FastAPI(
    title="String Analyzer Service",
    description="A RESTful API to analyze strings and store their computed properties.",
    version="1.0.0",
)


@app.post(
    "/strings", response_model=StringAnalyzerResult, status_code=status.HTTP_201_CREATED
)
async def create_string(input_data: StringInput):
    """
    Analyzes a string, stores its properties, and returns the result.

    Args:
        input_data: The string to be analyzed.

    Raises:
        HTTPException: If the input string is empty or already exists in the system.

    Returns:
        The result of the string analysis.
    """
    if not input_data.value.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The 'value' field cannot be empty or whitespace.",
        )

    properties_data = analyse_string(input_data.value)
    sha256_hash = properties_data["sha256_hash"]

    if sha256_hash in DATABASE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="String already exists in the system",
        )

    properties_model = StringProperties(**properties_data)

    result = StringAnalyzerResult(
        id=sha256_hash,
        value=input_data.value,
        properties=properties_model,
        created_at=datetime.now(timezone.utc),
    )

    DATABASE[sha256_hash] = result

    return result


@app.get("/strings/{string_value}", response_model=StringAnalyzerResult)
async def get_string_by_value(string_value: str):
    """
    Retrieves a specific analyzed string using its original value.

    The string value is hashed to find the corresponding analysis result in the database.

    Args:
        string_value: The original string value to retrieve.

    Raises:
        HTTPException: If the string is not found in the system.

    Returns:
        The stored analysis result for the given string.
    """

    temp_properties = analyse_string(string_value)
    sha256_hash = temp_properties["sha256_hash"]

    if sha256_hash not in DATABASE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="String does not exist in the system.",
        )

    return DATABASE[sha256_hash]


class FilteredStringsResponse(BaseModel):
    """
    Model for the response when retrieving a filtered list of strings.

    Attributes:
        data: A list of string analysis results that match the filter criteria.
        count: The number of results returned.
        filters_applied: A dictionary of the filters that were applied to the query.
    """

    data: List[StringAnalyzerResult]
    count: int
    filters_applied: Dict[str, Any]


@app.get("/strings", response_model=FilteredStringsResponse)
async def get_all_strings_with_filtering(
    is_palindrome: Optional[bool] = Query(
        None, description="Filter by palindrome status (true/false)"
    ),
    min_length: Optional[int] = Query(
        None, ge=1, description="Minimum string length (inclusive)"
    ),
    max_length: Optional[int] = Query(
        None, ge=1, description="Maximum string length (inclusive)"
    ),
    word_count: Optional[int] = Query(None, ge=1, description="Exact word count"),
    contains_character: Optional[str] = Query(
        None,
        min_length=1,
        max_length=1,
        description="Single character the string must contain",
    ),
):
    """
    Retrieves all stored strings with optional filtering based on properties.

    Args:
        is_palindrome: Filter by palindrome status.
        min_length: Filter by minimum string length.
        max_length: Filter by maximum string length.
        word_count: Filter by exact word count.
        contains_character: Filter by a character that the string must contain.

    Returns:
        A response object containing the filtered list of strings, the count of results,
        and the filters that were applied.
    """

    # Store applied filters for the response
    applied_filters = {
        k: v
        for k, v in locals().items()
        if k != "self" and v is not None and k not in ["DATABASE"]
    }

    # Start with all strings from the in-memory database
    filtered_results = list(DATABASE.values())

    # Apply filters sequentially

    # Filter by palindrome status
    if is_palindrome is not None:
        filtered_results = [
            r for r in filtered_results if r.properties.is_palindrome == is_palindrome
        ]

    # Filter by minimum length
    if min_length is not None:
        filtered_results = [
            r for r in filtered_results if r.properties.length >= min_length
        ]

    # Filter by maximum length
    if max_length is not None:
        filtered_results = [
            r for r in filtered_results if r.properties.length <= max_length
        ]

    # Filter by exact word count
    if word_count is not None:
        filtered_results = [
            r for r in filtered_results if r.properties.word_count == word_count
        ]

    # Filter by a character that the string must contain
    if contains_character is not None:
        # Case-insensitive check on the original string
        char_lower = contains_character.lower()
        filtered_results = [
            r for r in filtered_results if char_lower in r.value.lower()
        ]

    # Note: FastAPI's Pydantic validation handles 400 Bad Request for incorrect types

    return FilteredStringsResponse(
        data=filtered_results,
        count=len(filtered_results),
        filters_applied=applied_filters,
    )


# Helper model for the NL response
class NaturalLanguageResponse(BaseModel):
    data: List[StringAnalyzerResult]
    count: int
    interpreted_query: Dict[str, Any]


def parse_natural_language_query(query: str) -> Dict[str, Any]:
    """Basic NLP-like parser to convert text query to structured filters."""

    # Normalize for easier parsing
    q = query.lower().strip()
    filters = {}

    # --- Palindrome check ---
    if "palindromic" in q or "palindrome" in q:
        filters["is_palindrome"] = True
    elif "non-palindromic" in q:
        filters["is_palindrome"] = False

    # --- Word Count check ---
    if "single word" in q:
        filters["word_count"] = 1
    elif "two words" in q or "2 words" in q:
        filters["word_count"] = 2

    # --- Length checks ---
    # Example: "longer than 10 characters" -> min_length=11
    if "longer than" in q:
        try:
            # Find the number after "longer than"
            num_str = q.split("longer than")[1].split()[0]
            filters["min_length"] = int(num_str) + 1
        except (ValueError, IndexError):
            pass  # Ignore if parsing fails

    # --- Contains Character checks ---
    if "containing the letter" in q:
        try:
            char = (
                q.split("containing the letter")[1]
                .split()[0]
                .replace('"', "")
                .replace("'", "")
            )
            if len(char) == 1 and char.isalpha():
                filters["contains_character"] = char
        except (ValueError, IndexError):
            pass

    elif "contain the first vowel" in q:
        filters["contains_character"] = "a"

    elif "contains" in q:
        # Simple extraction for generic 'contains'
        parts = q.split("contains")
        if len(parts) > 1:
            try:
                char = (
                    parts[1]
                    .strip()
                    .split()[0]
                    .strip(".,:;")
                    .replace('"', "")
                    .replace("'", "")
                )
                if len(char) == 1 and char.isalpha():
                    filters["contains_character"] = char
            except IndexError:
                pass

    return filters


@app.get("/strings/filter-by-natural-language", response_model=NaturalLanguageResponse)
async def natural_language_filtering(
    query: str = Query(..., description="Natural language filter query"),
):
    """Filters strings based on a natural language query."""

    try:
        parsed_filters = parse_natural_language_query(query)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to parse natural language query.",
        )

    if not parsed_filters:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parsed but resulted in no recognized filters.",
        )

    # Re-use the filtering logic from the /strings endpoint, but directly
    filtered_results = list(DATABASE.values())

    # 1. is_palindrome
    if "is_palindrome" in parsed_filters:
        flag = parsed_filters["is_palindrome"]
        filtered_results = [
            r for r in filtered_results if r.properties.is_palindrome == flag
        ]

    # 2. word_count
    if "word_count" in parsed_filters:
        count = parsed_filters["word_count"]
        filtered_results = [
            r for r in filtered_results if r.properties.word_count == count
        ]

    # 3. min_length
    if "min_length" in parsed_filters:
        length = parsed_filters["min_length"]
        filtered_results = [
            r for r in filtered_results if r.properties.length >= length
        ]

    # 4. contains_character
    if "contains_character" in parsed_filters:
        char_lower = parsed_filters["contains_character"].lower()
        filtered_results = [
            r for r in filtered_results if char_lower in r.value.lower()
        ]

    return NaturalLanguageResponse(
        data=filtered_results,
        count=len(filtered_results),
        interpreted_query={"original": query, "parsed_filters": parsed_filters},
    )


@app.delete("/strings/{string_value}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_string_by_value(string_value: str):
    """
    Deletes a specific analyzed string using its original value.

    The string value is hashed to find and delete the corresponding analysis result
    from the database.

    Args:
        string_value: The original string value to delete.

    Raises:
        HTTPException: If the string is not found in the system.
    """

    temp_properties = analyse_string(string_value)
    sha256_hash = temp_properties["sha256_hash"]

    if sha256_hash not in DATABASE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="String does not exist in the system.",
        )

    del DATABASE[sha256_hash]
