"""
Test script for retry behavior with custom exceptions
"""

import time
from core.decorators import retry_on_retriable
from core.exceptions import RetriableError
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Counter for tracking retries
attempt_counter = {"count": 0}


@retry_on_retriable(max_attempts=3, delay=0.5, backoff=2.0)
def failing_function_retriable():
    """Simula falha retriable que deve fazer retry"""
    attempt_counter["count"] += 1
    print(f"Attempt {attempt_counter['count']}: Raising RetriableError")
    raise RetriableError("Simulated network timeout")


@retry_on_retriable(max_attempts=3, delay=0.5)
def succeeding_function_after_2():
    """Sucede na 2ª tentativa"""
    attempt_counter["count"] += 1
    print(f"Attempt {attempt_counter['count']}")
    if attempt_counter["count"] < 2:
        raise RetriableError("Temporary failure")
    print("Success!")
    return "OK"


def test_retry_exhaustion():
    """Testa se retry é esgotado após max_attempts"""
    print("\n=== Test 1: Retry Exhaustion ===")
    attempt_counter["count"] = 0
    try:
        failing_function_retriable()
        print("❌ FAILED: Should have raised RetriableError after 3 attempts")
        return False
    except RetriableError:
        if attempt_counter["count"] == 3:
            print(
                f"✅ PASSED: Retried {
                    attempt_counter['count']} times as expected")
            return True
        else:
            print(
                f"❌ FAILED: Expected 3 attempts but got {
                    attempt_counter['count']}")
            return False


def test_retry_success():
    """Testa se retry para quando sucede"""
    print("\n=== Test 2: Retry Success ===")
    attempt_counter["count"] = 0
    try:
        result = succeeding_function_after_2()
        if attempt_counter["count"] == 2 and result == "OK":
            print(f"✅ PASSED: Succeeded on attempt {attempt_counter['count']}")
            return True
        else:
            print(f"❌ FAILED: Expected success on attempt 2")
            return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected exception: {e}")
        return False


def test_exception_chain():
    """Testa se exception chain é preservada"""
    print("\n=== Test 3: Exception Chain ===")
    try:
        original_error = ConnectionError("Network unreachable")
        raise RetriableError("Qdrant connection failed") from original_error
    except RetriableError as e:
        if e.__cause__ and isinstance(e.__cause__, ConnectionError):
            print("✅ PASSED: Exception chain preserved")
            return True
        else:
            print("❌ FAILED: Exception chain not preserved")
            return False


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Retry Behavior with Custom Exceptions")
    print("=" * 60)

    results = []
    results.append(test_retry_exhaustion())
    results.append(test_retry_success())
    results.append(test_exception_chain())

    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)

    sys.exit(0 if all(results) else 1)
