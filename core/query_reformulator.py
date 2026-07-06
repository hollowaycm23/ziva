#!/usr/bin/env python3
"""
Query Reformulator - Reformulates ambiguous queries for better results.
"""

import re
import logging
from typing import List, Optional


logger = logging.getLogger("QueryReformulator")


class QueryReformulator:
    """
    Reformulates queries to improve success rate.
    """

    QUESTION_WORDS = [
        "o que", "qual", "quem", "como", "quando", "onde", "por que"]
    CONTEXT_KEYWORDS = [
        "informações sobre", "definição de", "explicação sobre",
        "dados sobre", "detalhes sobre"
    ]
    ABBREVIATIONS = {
        "sp": "são paulo", "rj": "rio de janeiro", "mg": "minas gerais",
        "br": "brasil", "eua": "estados unidos", "uk": "reino unido"
    }

    def __init__(self):
        """Initialize query reformulator."""
        logger.info("QueryReformulator initialized")

    def reformulate(
        self,
        query: str,
        failed_attempts: List[str] = None
    ) -> List[str]:
        """
        Generate query variations.
        """
        failed_attempts = failed_attempts or []
        variations = []
        query_lower = query.lower().strip()

        if not self._has_question_word(query_lower):
            variations.extend(self._add_question_words(query))
        variations.extend(self._add_context_keywords(query))
        expanded = self._expand_abbreviations(query)
        if expanded != query:
            variations.append(expanded)
        if len(query.split()) > 10:
            simplified = self._simplify_query(query)
            if simplified:
                variations.append(simplified)
        cleaned = self._remove_ambiguous_words(query)
        if cleaned != query:
            variations.append(cleaned)
        variations = [v for v in variations if v not in failed_attempts]
        seen = set()
        unique_variations = []
        for v in variations:
            if v.lower() not in seen:
                seen.add(v.lower())
                unique_variations.append(v)
        logger.info(f"Generated {len(unique_variations)} query variations")
        return unique_variations[:5]

    def _has_question_word(self, query: str) -> bool:
        return any(qw in query for qw in self.QUESTION_WORDS)

    def _add_question_words(self, query: str) -> List[str]:
        variations = []
        variations.append(f"o que é {query}")
        if not query.startswith("qual"):
            variations.append(f"qual {query}")
        if self._might_be_person(query):
            variations.append(f"quem é {query}")
        return variations

    def _add_context_keywords(self, query: str) -> List[str]:
        variations = []
        for keyword in self.CONTEXT_KEYWORDS[:3]:
            variations.append(f"{keyword} {query}")
        return variations

    def _expand_abbreviations(self, query: str) -> str:
        expanded = query
        for abbr, full in self.ABBREVIATIONS.items():
            pattern = r'\b' + re.escape(abbr) + r'\b'
            expanded = re.sub(pattern, full, expanded, flags=re.IGNORECASE)
        return expanded

    def _simplify_query(self, query: str) -> Optional[str]:
        filler_words = [
            "por favor", "gostaria de saber", "pode me dizer", "quero saber"]
        simplified = query
        for filler in filler_words:
            simplified = simplified.replace(filler, "")
        simplified = " ".join(simplified.split())
        return simplified if simplified != query else None

    def _remove_ambiguous_words(self, query: str) -> str:
        ambiguous = ["aquilo", "isso", "aquele", "esse", "este"]
        cleaned = query
        for word in ambiguous:
            cleaned = re.sub(
                r'\b' + word + r'\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = " ".join(cleaned.split())
        return cleaned

    def _might_be_person(self, query: str) -> bool:
        person_indicators = [
            "einstein", "newton", "darwin", "presidente", "cientista",
            "autor", "escritor", "artista", "músico", "ator"
        ]
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in person_indicators)
