#!/usr/bin/env python3
"""
Example usage of Ziva's Response Validation System.

Demonstrates how to use ResponseValidator, QueryClassifier, and FallbackChain.
"""

import logging
from core.response_validator import ResponseValidator
from core.query_classifier import QueryClassifier
from core.fallback_chain import FallbackChain

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("ValidationExample")


def example_1_response_validation():
    """Example 1: Validate response quality."""
    logger.info("=== Example 1: Response Validation ===")

    validator = ResponseValidator(min_confidence=0.7)

    # Test 1: Generic response (should fail)
    generic_response = "Desculpe, não sei responder essa pergunta."
    result = validator.validate_response(
        generic_response, "qual a temperatura")

    logger.info(f"Generic response valid: {result.is_valid}")
    logger.info(f"Status: {result.status.value}")
    logger.info(f"Reason: {result.reason}")

    # Test 2: Good response (should pass)
    good_response = "A temperatura em São Paulo é de 25°C, com céu parcialmente nublado."
    result = validator.validate_response(
        good_response,
        "qual a temperatura em são paulo",
        tools_used=["get_weather"]
    )

    logger.info(f"\nGood response valid: {result.is_valid}")
    logger.info(f"Confidence: {result.confidence:.2f}")


def example_2_query_classification():
    """Example 2: Classify queries."""
    logger.info("\n=== Example 2: Query Classification ===")

    classifier = QueryClassifier()

    queries = [
        "qual a temperatura em são paulo",
        "que horas são",
        "quem foi albert einstein",
        "como fazer um loop em python"
    ]

    for query in queries:
        result = classifier.classify(query)
        logger.info(f"\nQuery: '{query}'")
        logger.info(f"Type: {result.query_type.value}")
        logger.info(f"Optimal tools: {result.optimal_tools}")


def example_3_fallback_chain():
    """Example 3: Fallback chain execution."""
    logger.info("\n=== Example 3: Fallback Chain ===")

    # Mock tools for demonstration
    def mock_weather(location=None):
        return f"Temperatura em {location or 'localização'}: 25°C"

    def mock_datetime():
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

    # Create fallback chain
    chain = FallbackChain(
        weather=mock_weather,
        datetime_tool=mock_datetime
    )

    # Test weather query
    result = chain.execute("qual a temperatura em são paulo")
    logger.info(f"\nWeather query result:")
    logger.info(f"Response: {result.response}")
    logger.info(f"Tool used: {result.successful_tool}")
    logger.info(f"Attempts: {result.attempts}")

    # Test datetime query
    result = chain.execute("que horas são")
    logger.info(f"\nDatetime query result:")
    logger.info(f"Response: {result.response}")
    logger.info(f"Tool used: {result.successful_tool}")


def example_4_complete_workflow():
    """Example 4: Complete validation workflow."""
    logger.info("\n=== Example 4: Complete Workflow ===")

    validator = ResponseValidator()
    classifier = QueryClassifier()

    query = "qual o clima em são paulo"

    # Step 1: Classify
    classification = classifier.classify(query)
    logger.info(f"Query type: {classification.query_type.value}")

    # Step 2: Get mock response
    response = "O clima em São Paulo está com temperatura de 25°C, parcialmente nublado."

    # Step 3: Validate
    validation = validator.validate_response(
        response,
        query,
        tools_used=["get_weather"]
    )

    logger.info(f"Response valid: {validation.is_valid}")
    logger.info(f"Confidence: {validation.confidence:.2f}")

    if not validation.is_valid:
        logger.warning(f"Validation failed: {validation.reason}")
        logger.info(f"Suggestions: {validation.suggestions}")


if __name__ == "__main__":
    """Run all examples."""

    print("\n" + "=" * 60)
    print("Ziva Response Validation System - Examples")
    print("=" * 60 + "\n")

    try:
        example_1_response_validation()
        example_2_query_classification()
        example_3_fallback_chain()
        example_4_complete_workflow()

        print("\n" + "=" * 60)
        print("All examples completed!")
        print("=" * 60 + "\n")

    except KeyboardInterrupt:
        logger.info("\nExecution interrupted by user")
    except Exception as e:
        logger.error(f"\nError during examples: {e}")
