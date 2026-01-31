#!/usr/bin/env python3
"""
Response Validator - Validates quality of Ziva's responses.
"""

import re
import logging
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger("ResponseValidator")


class ValidationStatus(Enum):
    """Response validation status."""
    VALID = "valid"
    GENERIC = "generic"
    EMPTY = "empty"
    LOW_CONFIDENCE = "low_confidence"
    NO_FACTS = "no_facts"


@dataclass
class ValidationResult:
    """
    Result of response validation.
    """
    is_valid: bool
    status: ValidationStatus
    confidence: float
    reason: str
    suggestions: List[str]


class ResponseValidator:
    """
    Validates quality of Ziva's responses.
    """

    GENERIC_PHRASES = [
        "não sei", "não tenho informação", "não posso responder",
        "desculpe, não", "infelizmente não", "não está disponível",
        "não consigo", "sem informações", "não encontrei",
        "não há dados", "informação indisponível", "não possuo",
        "não conheço", "não tenho acesso", "não foi possível",
        "erro ao buscar", "falha ao obter"
    ]

    FACTUAL_INDICATORS = [
        "de acordo com", "segundo", "conforme", "baseado em",
        "fonte:", "referência:", "dados de", "informação de",
        "temperatura", "clima", "previsão", "°c", "graus", "km/h",
        "mm", "%"
    ]

    def __init__(self, min_confidence: float = 0.7):
        """
        Initialize response validator.
        """
        self.min_confidence = min_confidence
        logger.info(
            f"ResponseValidator initialized (min_confidence={min_confidence})")

    def validate_response(
        self,
        response: str,
        query: str,
        tools_used: Optional[List[str]] = None
    ) -> ValidationResult:
        """
        Validate a response.
        """
        tools_used = tools_used or []
        if not response or len(response.strip()) < 10:
            return ValidationResult(
                is_valid=False, status=ValidationStatus.EMPTY,
                confidence=0.0, reason="Response is empty or too short",
                suggestions=["Use fallback tools", "Try alternative search"]
            )
        if self.is_generic(response):
            return ValidationResult(
                is_valid=False, status=ValidationStatus.GENERIC,
                confidence=0.2, reason="Response contains generic phrases",
                suggestions=["Try web search", "Use Kiwix", "Consult RAG"]
            )
        has_facts = self.has_factual_content(response)
        confidence = self.calculate_confidence(response, tools_used, has_facts)
        is_valid = confidence >= self.min_confidence and has_facts
        if not is_valid:
            if not has_facts:
                status = ValidationStatus.NO_FACTS
                reason = "Response lacks factual content"
                suggestions = ["Add sources", "Include specific data"]
            else:
                status = ValidationStatus.LOW_CONFIDENCE
                reason = f"Confidence too low: {confidence:.2f}"
                suggestions = [
                    "Use more reliable tools", "Cross-reference sources"]
        else:
            status = ValidationStatus.VALID
            reason = "Response meets quality standards"
            suggestions = []
        return ValidationResult(
            is_valid=is_valid,
            status=status,
            confidence=confidence,
            reason=reason,
            suggestions=suggestions
        )

    def is_generic(self, response: str) -> bool:
        """
        Check if response contains generic phrases.
        """
        response_lower = response.lower()
        for phrase in self.GENERIC_PHRASES:
            if phrase in response_lower:
                logger.warning(f"Generic phrase detected: '{phrase}'")
                return True
        return False

    def has_factual_content(self, response: str) -> bool:
        """
        Check if response contains factual content.
        """
        response_lower = response.lower()
        for indicator in self.FACTUAL_INDICATORS:
            if indicator in response_lower:
                return True
        if re.search(r'\d+', response):
            return True
        if re.search(r'\d{1,2}/\d{1,2}/\d{2,4}', response):
            return True
        if re.search(r'https?://', response):
            return True
        if len(response) > 200:
            return True
        return False

    def calculate_confidence(
        self,
        response: str,
        tools_used: List[str],
        has_facts: bool
    ) -> float:
        """
        Calculate confidence score for response.
        """
        confidence = 0.5
        if has_facts:
            confidence += 0.2
        tool_scores = {
            "get_weather": 0.3,
            "get_datetime": 0.3,
            "search_web": 0.2,
            "search_kiwix": 0.15,
            "rag_search": 0.1
        }
        for tool in tools_used:
            confidence += tool_scores.get(tool, 0.05)
        if len(response) > 300:
            confidence += 0.1
        elif len(response) > 150:
            confidence += 0.05
        if len(response) < 50:
            confidence -= 0.2
        confidence = max(0.0, min(1.0, confidence))
        return confidence

    def suggest_improvements(
        self,
        response: str,
        query: str,
        validation: ValidationResult
    ) -> List[str]:
        """
        Suggest improvements for a response.
        """
        suggestions = []
        if validation.status == ValidationStatus.GENERIC:
            suggestions.append("Use specific tools (weather, web search, RAG)")
            suggestions.append("Avoid phrases like 'não sei'")
        if validation.status == ValidationStatus.NO_FACTS:
            suggestions.append("Include specific data, numbers, or sources")
            suggestions.append("Reference where information came from")
        if validation.status == ValidationStatus.LOW_CONFIDENCE:
            suggestions.append("Use multiple tools to cross-reference")
            suggestions.append("Provide more detailed information")
        if len(response) < 100:
            suggestions.append("Expand response with more details")
        return suggestions

    def validate_tool_result(
        self,
        tool_name: str,
        tool_result: str
    ) -> bool:
        """
        Validate result from a specific tool.
        """
        if not tool_result or len(tool_result.strip()) < 5:
            logger.warning(f"Tool {tool_name} returned empty result")
            return False
        error_indicators = ["error", "erro", "falha", "failed", "exception"]
        result_lower = tool_result.lower()
        for indicator in error_indicators:
            if indicator in result_lower:
                logger.warning(
                    f"Tool {tool_name} returned error: {tool_result[:100]}")
                return False
        if tool_name == "get_weather":
            if "temperatura" not in result_lower and "temperature" not in result_lower:
                return False
        elif tool_name == "get_datetime":
            if not re.search(r'\d{1,2}:\d{2}', tool_result):
                return False
        return True