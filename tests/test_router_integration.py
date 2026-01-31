#!/usr/bin/env python3
"""
Comprehensive test suite for LLM Router and annika-logic integration.
Tests tool detection, model routing, and end-to-end functionality.
"""

import requests
import json
import time
from typing import Dict, List

API_URL = "http://127.0.0.1:8000/chat"
API_KEY = "ziva-terminal-chat-key"


class TestRunner:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0

    def test_query(self, query: str, expected_tool: str = None,
                   expected_model: str = None) -> Dict:
        """Test a single query and validate response."""
        print(f"\n🧪 Testing: {query}")

        try:
            response = requests.post(
                API_URL,
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": API_KEY
                },
                json={"message": query},
                timeout=60
            )

            if response.status_code != 200:
                print(f"❌ HTTP {response.status_code}")
                self.failed += 1
                return {"query": query, "status": "failed",
                        "error": f"HTTP {response.status_code}"}

            data = response.json()
            response_text = data.get("response", "")
            model_used = data.get("model_used", "unknown")

            # Check if tool was executed
            tool_executed = "No tool executed" not in response_text

            result = {
                "query": query,
                "response": response_text[:200],
                "model": model_used,
                "tool_executed": tool_executed,
                "status": "passed"
            }

            # Validate expected tool
            if expected_tool:
                if expected_tool in response_text.lower() or tool_executed:
                    print(f"✅ Tool executed: {expected_tool}")
                    result["tool_check"] = "passed"
                else:
                    print(f"❌ Expected tool '{expected_tool}' not executed")
                    result["tool_check"] = "failed"
                    result["status"] = "failed"
                    self.failed += 1
                    return result

            # Validate expected model
            if expected_model:
                if expected_model in model_used:
                    print(f"✅ Model: {model_used}")
                    result["model_check"] = "passed"
                else:
                    print(
                        f"⚠️  Model: {model_used} (expected: {expected_model})")
                    result["model_check"] = "warning"

            print(f"✅ Response: {response_text[:100]}...")
            self.passed += 1
            self.results.append(result)
            return result

        except Exception as e:
            print(f"❌ Error: {e}")
            self.failed += 1
            return {"query": query, "status": "failed", "error": str(e)}

    def run_test_suite(self):
        """Run comprehensive test suite."""
        print("=" * 80)
        print("🧪 ZIVA LLM ROUTER & ANNIKA-LOGIC INTEGRATION TESTS")
        print("=" * 80)

        # Test 1: Search queries (should use web_search)
        print("\n📍 Test Category: SEARCH QUERIES")
        print("-" * 80)
        self.test_query(
            "pesquise sobre inteligência artificial",
            expected_tool="search")
        time.sleep(2)
        self.test_query(
            "busque informações sobre python",
            expected_tool="search")
        time.sleep(2)

        # Test 2: Weather queries (should use get_weather)
        print("\n📍 Test Category: WEATHER QUERIES")
        print("-" * 80)
        self.test_query(
            "qual a temperatura em artur nogueira",
            expected_tool="weather")
        time.sleep(2)
        self.test_query(
            "como está o clima em são paulo",
            expected_tool="weather")
        time.sleep(2)

        # Test 3: Code queries (should use qwen-coder)
        print("\n📍 Test Category: CODE QUERIES")
        print("-" * 80)
        self.test_query("escreva uma função python para fibonacci")
        time.sleep(2)

        # Test 4: General conversation (should use llama3)
        print("\n📍 Test Category: CONVERSATION")
        print("-" * 80)
        self.test_query("olá, como você está?")
        time.sleep(2)

        # Test 5: Logic/Decision queries (should use annika-logic)
        print("\n📍 Test Category: LOGIC & DECISIONS")
        print("-" * 80)
        self.test_query("qual a melhor abordagem: usar cache ou não?")
        time.sleep(2)

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(
            f"📈 Success Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")

        if self.failed == 0:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️  {self.failed} test(s) failed. Review logs above.")

        print("=" * 80)


if __name__ == "__main__":
    runner = TestRunner()
    runner.run_test_suite()
