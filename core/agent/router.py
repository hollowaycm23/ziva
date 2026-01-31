"""
Query routing utilities for the Ziva agent.
Determines which specialized search to use based on query content.
"""
from typing import Literal


def is_anime_query(question: str) -> bool:
    """
    Detect if a query is anime-related.

    Args:
        question: User's question

    Returns:
        True if anime-related, False otherwise
    """
    question_lower = question.lower()

    # Direct anime keywords
    anime_keywords = [
        'anime', 'manga', 'mangá',
        'otaku', 'cosplay',
        'studio', 'estúdio',
        'temporada de anime',
        'série de anime',
        'personagem de anime',
        'anime sobre',
    ]

    # Anime genres/types
    anime_genres = [
        'shounen', 'shonen',
        'seinen', 'shoujo', 'shojo',
        'isekai', 'mecha',
        'slice of life',
        'magical girl',
    ]

    # Anime-specific terms
    anime_terms = [
        'naruto', 'one piece', 'dragon ball',
        'attack on titan', 'shingeki',
        'death note', 'fullmetal',
        'my hero academia', 'demon slayer',
        'sword art online', 'evangelion',
    ]

    # Check all categories
    all_keywords = anime_keywords + anime_genres + anime_terms

    return any(keyword in question_lower for keyword in all_keywords)


def is_sherlock_query(question: str) -> bool:
    """
    Detect if query is requesting OSINT/username search.

    Args:
        question: User's question

    Returns:
        True if OSINT-related, False otherwise
    """
    question_lower = question.lower()

    sherlock_keywords = [
        'sherlock',
        'procurar usuário',
        'buscar usuário',
        'redes sociais',
        'perfil de',
        'username',
    ]

    return any(keyword in question_lower for keyword in sherlock_keywords)


def route_query(question: str) -> Literal[
        "anime_search", "sherlock_search", "web_search"]:
    """
    Route query to appropriate search tool.

    Priority:
    1. Sherlock (OSINT) - highest priority for username searches
    2. Anime - specialized anime database
    3. Web Search - default fallback

    Args:
        question: User's question

    Returns:
        Name of search node to use
    """
    # Check in priority order
    if is_sherlock_query(question):
        return "sherlock_search"

    if is_anime_query(question):
        return "anime_search"

    # Default to web search
    return "web_search"
