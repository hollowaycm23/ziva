#!/usr/bin/env python3
"""
Context Expander - Expands queries using conversation history.
"""

import re
import logging
from typing import List, Optional


logger = logging.getLogger("ContextExpander")


class ContextExpander:
    """
    Expands queries using conversation context.
    """

    PRONOUNS = ["ele", "ela", "isso", "aquilo", "este", "esse"]
    FOLLOWUP_PATTERNS = [
        r"^quando ",
        r"^onde ",
        r"^como ",
        r"^por que ",
        r"^quem ",
        r"^qual "
    ]

    def __init__(self):
        """Initialize context expander."""
        self.conversation_history = []
        self.last_entities = {
            "person": None,
            "place": None,
            "thing": None
        }
        logger.info("ContextExpander initialized")

    def add_to_history(self, query: str, response: str):
        """
        Add query/response to conversation history.
        """
        self.conversation_history.append({
            "query": query,
            "response": response
        })
        self._extract_entities(query)
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]

    def expand_query(self, query: str) -> str:
        """
        Expand query with context if needed.
        """
        if not self.conversation_history:
            return query
        query_lower = query.lower().strip()
        if not self._is_ambiguous(query_lower):
            return query
        expanded = self._replace_pronouns(query)
        if self._is_followup_question(query_lower):
            expanded = self._add_followup_context(expanded)
        if expanded != query:
            logger.info(f"Expanded query: '{query}' → '{expanded}'")
        return expanded

    def _is_ambiguous(self, query: str) -> bool:
        """Check if query is ambiguous."""
        if any(pronoun in query for pronoun in self.PRONOUNS):
            return True
        if len(query.split()) <= 2:
            return True
        if self._is_followup_question(query):
            return True
        return False

    def _is_followup_question(self, query: str) -> bool:
        """Check if query is a follow-up question."""
        return any(re.match(pattern, query)
                   for pattern in self.FOLLOWUP_PATTERNS)

    def _replace_pronouns(self, query: str) -> str:
        """Replace pronouns with last mentioned entity."""
        expanded = query
        for pronoun in self.PRONOUNS:
            if pronoun in query.lower():
                entity = self._get_appropriate_entity(pronoun)
                if entity:
                    pattern = r'\b' + re.escape(pronoun) + r'\b'
                    expanded = re.sub(
                        pattern, entity, expanded, flags=re.IGNORECASE, count=1)
        return expanded

    def _add_followup_context(self, query: str) -> str:
        """Add context for follow-up questions."""
        if not self.conversation_history:
            return query
        last_exchange = self.conversation_history[-1]
        last_query = last_exchange["query"]
        subject = self._extract_main_subject(last_query)
        if subject:
            expanded = f"{query} {subject}"
            return expanded
        return query

    def _extract_entities(self, text: str):
        """Extract and track entities from text."""
        words = text.split()
        for word in words:
            if word and word[0].isupper() and len(word) > 2:
                if self._is_person_name(word):
                    self.last_entities["person"] = word
                elif self._is_place_name(word):
                    self.last_entities["place"] = word
                else:
                    self.last_entities["thing"] = word

    def _get_appropriate_entity(self, pronoun: str) -> Optional[str]:
        """Get appropriate entity for pronoun."""
        pronoun_lower = pronoun.lower()
        if pronoun_lower in ["ele", "ela"]:
            return self.last_entities.get("person")
        elif pronoun_lower in ["isso", "aquilo"]:
            return self.last_entities.get("thing")
        for entity in self.last_entities.values():
            if entity:
                return entity
        return None

    def _extract_main_subject(self, query: str) -> Optional[str]:
        """Extract main subject from query."""
        cleaned = query
        for qw in ["o que é", "qual", "quem é", "como", "quando", "onde"]:
            cleaned = cleaned.replace(qw, "")
        cleaned = cleaned.strip()
        words = cleaned.split()
        if words:
            return " ".join(words[:3])
        return None

    def _is_person_name(self, word: str) -> bool:
        """Check if word is likely a person name."""
        person_suffixes = ["son", "sen", "stein", "berg"]
        return any(word.lower().endswith(suffix) for suffix in person_suffixes)

    def _is_place_name(self, word: str) -> bool:
        """Check if word is likely a place name."""
        place_keywords = ["paulo", "rio", "york", "london", "paris"]
        return any(keyword in word.lower() for keyword in place_keywords)

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        self.last_entities = {
            "person": None,
            "place": None,
            "thing": None
        }
        logger.info("Conversation history cleared")