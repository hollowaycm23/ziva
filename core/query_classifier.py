#!/usr/bin/env python3
"""
Query Classifier - Classifies user queries by type.
"""

import logging
from typing import List
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger("QueryClassifier")


class QueryType(Enum):
    """Types of user queries."""
    WEATHER = "weather"
    DATETIME = "datetime"
    FACTUAL = "factual"
    TECHNICAL = "technical"
    CONVERSATIONAL = "conversational"
    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    """
    Result of query classification.
    """
    query_type: QueryType
    confidence: float
    optimal_tools: List[str]
    keywords_matched: List[str]


class QueryClassifier:
    """
    Classifies user queries to determine optimal response strategy.
    """
    WEATHER_KEYWORDS = [
        "clima", "tempo", "temperatura", "previsão", "weather",
        "chuva", "sol", "nublado", "quente", "frio",
        "graus", "°c", "celsius", "fahrenheit",
        "vento", "umidade", "neblina"
    ]
    DATETIME_KEYWORDS = [
        "hora", "horas", "data", "dia", "hoje", "agora",
        "quando", "que dia", "calendário", "mês", "ano",
        "semana", "amanhã", "ontem", "time", "date"
    ]
    TECHNICAL_KEYWORDS = [
        "código", "programação", "python", "javascript", "java",
        "função", "classe", "método", "algoritmo", "debug",
        "erro", "exception", "syntax", "compile", "run",
        "install", "package", "library", "framework"
    ]
    CONVERSATIONAL_KEYWORDS = [
        "olá", "oi", "bom dia", "boa tarde", "boa noite",
        "tudo bem", "como vai", "obrigado", "valeu",
        "tchau", "até logo", "hello", "hi", "thanks"
    ]

    def __init__(self):
        """Initialize query classifier."""
        logger.info("QueryClassifier initialized")

    def classify(self, query: str) -> ClassificationResult:
        """
        Classify a query.
        """
        query_lower = query.lower()
        weather_match = self._check_weather(query_lower)
        datetime_match = self._check_datetime(query_lower)
        technical_match = self._check_technical(query_lower)
        conversational_match = self._check_conversational(query_lower)
        matches = [
            (QueryType.WEATHER, weather_match),
            (QueryType.DATETIME, datetime_match),
            (QueryType.TECHNICAL, technical_match),
            (QueryType.CONVERSATIONAL, conversational_match)
        ]
        matches.sort(key=lambda x: len(x[1]), reverse=True)
        if matches[0][1]:
            query_type = matches[0][0]
            keywords_matched = matches[0][1]
            confidence = min(1.0, len(keywords_matched) * 0.3)
        else:
            query_type = QueryType.FACTUAL
            keywords_matched = []
            confidence = 0.5
        optimal_tools = self.get_optimal_tools(query_type)
        logger.info(
            f"Classified as {query_type.value} "
            f"(confidence: {confidence:.2f})")
        return ClassificationResult(
            query_type=query_type,
            confidence=confidence,
            optimal_tools=optimal_tools,
            keywords_matched=keywords_matched
        )

    def _check_weather(self, query: str) -> List[str]:
        return [kw for kw in self.WEATHER_KEYWORDS if kw in query]

    def _check_datetime(self, query: str) -> List[str]:
        return [kw for kw in self.DATETIME_KEYWORDS if kw in query]

    def _check_technical(self, query: str) -> List[str]:
        return [kw for kw in self.TECHNICAL_KEYWORDS if kw in query]

    def _check_conversational(self, query: str) -> List[str]:
        return [kw for kw in self.CONVERSATIONAL_KEYWORDS if kw in query]

    def get_optimal_tools(self, query_type: QueryType) -> List[str]:
        tool_map = {
            QueryType.WEATHER: ["get_weather", "search_web"],
            QueryType.DATETIME: ["get_datetime"],
            QueryType.FACTUAL: ["rag_search", "search_kiwix", "search_web"],
            QueryType.TECHNICAL: [
                "rag_search", "search_web", "search_kiwix"],
            QueryType.CONVERSATIONAL: ["llm_direct"],
            QueryType.UNKNOWN: ["rag_search", "search_web"]
        }
        return tool_map.get(query_type, ["search_web"])

    def is_weather_query(self, query: str) -> bool:
        return len(self._check_weather(query.lower())) > 0

    def is_datetime_query(self, query: str) -> bool:
        return len(self._check_datetime(query.lower())) > 0

    def is_technical_query(self, query: str) -> bool:
        return len(self._check_technical(query.lower())) > 0