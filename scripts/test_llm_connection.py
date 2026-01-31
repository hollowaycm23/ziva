
import os
import dspy
from core.dspy_config import configure_dspy

# Force LM Studio backend for this test
os.environ["ZIVA_LLM_BACKEND"] = "lm_studio"
os.environ["ZIVA_LLM_BASE_URL"] = "http://localhost:1234/v1"
os.environ["ZIVA_LLM_MODEL"] = "qwen3-14b"

print("--- Testing LM Studio Connection ---")

try:
    lm, rm = configure_dspy()
    
    print("\nAttempting basic completion...")
    # Simple direct generation
    response = lm("Hello! Are you working?")
    print(f"\nResponse received:\n{response}")
    
    print("\n✅ Connection Test Passed!")
except Exception as e:
    print(f"\n❌ Connection Test Failed: {e}")
