#!/usr/bin/env python3
"""
Example usage of Ziva's Self-Healing Engine.

Demonstrates automatic code repair capabilities.
"""

import logging
from core.self_healing_engine import SelfHealingEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("SelfHealingExample")


def example_1_syntax_error_repair():
    """Example 1: Automatic syntax error repair."""
    logger.info("=== Example 1: Syntax Error Repair ===")

    # Code with syntax error (missing colon)
    broken_code = """
def calculate_sum(a, b)
    return a + b

result = calculate_sum(5, 3)
print(result)
"""

    # Create healing engine
    engine = SelfHealingEngine()

    # Repair code
    result = engine.repair_code(broken_code)

    if result.success:
        logger.info("✅ Code repaired successfully!")
        logger.info(f"Errors fixed: {len(result.errors_fixed)}")
        logger.info(f"Attempts: {len(result.attempts)}")
        logger.info(f"Duration: {result.total_duration_ms}ms")
        logger.info("\nRepaired code:")
        print(result.repaired_code)
    else:
        logger.error("❌ Repair failed")


def example_2_import_error_repair():
    """Example 2: Automatic import error repair."""
    logger.info("\n=== Example 2: Import Error Repair ===")

    # Code with missing import
    broken_code = """
import requests

def fetch_data():
    response = requests.get("https://api.example.com/data")
    df = pd.DataFrame(response.json())  # pandas not imported
    return df
"""

    engine = SelfHealingEngine()
    result = engine.repair_code(broken_code)

    if result.success:
        logger.info("✅ Import error fixed!")
        print(result.repaired_code)
    else:
        logger.warning("⚠️ Could not auto-fix (may need manual intervention)")


def example_3_logic_error_with_tests():
    """Example 3: Logic error detection with test cases."""
    logger.info("\n=== Example 3: Logic Error with Tests ===")

    # Code with logic error
    broken_code = """
def is_even(n):
    return n % 2 == 1  # Wrong logic!
"""

    # Test cases
    test_cases = [
        {"function": "is_even", "input": 2, "expected": True},
        {"function": "is_even", "input": 3, "expected": False},
        {"function": "is_even", "input": 4, "expected": True}
    ]

    engine = SelfHealingEngine()
    result = engine.repair_code(
        broken_code,
        run_tests=True,
        test_cases=test_cases)

    logger.info(f"Errors detected: {len(result.errors_fixed)}")
    for error in result.errors_fixed:
        logger.info(f"  - {error.category.value}: {error.message}")


def example_4_iterative_repair():
    """Example 4: Multiple errors requiring iterative repair."""
    logger.info("\n=== Example 4: Iterative Repair ===")

    # Code with multiple errors
    broken_code = """
def process_data(data)  # Missing colon
    if data is None
        return []  # Missing colon

    result = []
    for item in data:
        result.append(item * 2
    return result  # Missing closing parenthesis
"""

    engine = SelfHealingEngine(max_attempts=10)
    result = engine.repair_code(broken_code)

    logger.info(f"Total attempts: {len(result.attempts)}")
    logger.info(f"Errors fixed: {len(result.errors_fixed)}")
    logger.info(f"Success: {result.success}")

    if result.success:
        print("\nRepaired code:")
        print(result.repaired_code)


def example_5_detect_only():
    """Example 5: Error detection without repair."""
    logger.info("\n=== Example 5: Error Detection Only ===")

    code = """
def divide(a, b):
    return a / b  # Potential ZeroDivisionError

result = divide(10, 0)
"""

    engine = SelfHealingEngine()
    errors = engine.detect_errors(code)

    logger.info(f"Detected {len(errors)} potential errors:")
    for error in errors:
        logger.info(
            f"  - {error.category.value} ({error.severity.value}): {error.message}")
        if error.suggested_fix:
            logger.info(f"    Suggested fix: {error.suggested_fix}")


if __name__ == "__main__":
    """Run all examples."""

    print("\n" + "=" * 60)
    print("Ziva Self-Healing Engine - Examples")
    print("=" * 60 + "\n")

    try:
        example_1_syntax_error_repair()
        example_2_import_error_repair()
        example_3_logic_error_with_tests()
        example_4_iterative_repair()
        example_5_detect_only()

        print("\n" + "=" * 60)
        print("All examples completed!")
        print("=" * 60 + "\n")

    except KeyboardInterrupt:
        logger.info("\nExecution interrupted by user")
    except Exception as e:
        logger.error(f"\nError during examples: {e}")
