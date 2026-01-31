
print("Starting Verification...")

try:
    print("Test 1: Importing Modules...")
    from tools.validators.tool_validator import ToolValidator
    from tools.runtime.tool_runtime import ToolRuntime
    from rag.retrieval.research_augmenter import get_research_augmenter
    from core.memory.ziva_memory import ZivaMemory
    print("SUCCESS: Modules imported correctly.")
except ImportError as e:
    print(f"FAILED: Import error: {e}")
    exit(1)

try:
    print("\nTest 2: ToolValidator...")
    validator = ToolValidator()

    # Safe code
    safe_code = "def test(a): return {'res': a * 2}"
    valid, errors = validator.validate(safe_code)
    if not valid:
        print(f"FAILED: Safe code marked invalid: {errors}")
        exit(1)

    # Unsafe code
    unsafe_code = "import os; os.system('ls')"
    valid, errors = validator.validate(unsafe_code)
    if valid:
        print("FAILED: Unsafe code marked valid!")
        exit(1)
    print("SUCCESS: ToolValidator works.")
except Exception as e:
    print(f"FAILED: Validator threw exception: {e}")
    exit(1)

try:
    print("\nTest 3: ToolRuntime...")
    runtime = ToolRuntime()

    code = """
def multiply(a, b):
    return {"result": a * b}
"""
    result, error = runtime.execute_tool(code, "multiply", {"a": 5, "b": 3})

    if error:
        print(f"FAILED: Runtime execution error: {error}")
        exit(1)

    if result.get("result") != 15:
        print(f"FAILED: Expected 15, got {result}")
        exit(1)

    print("SUCCESS: ToolRuntime works.")
except Exception as e:
    print(f"FAILED: Runtime threw exception: {e}")
    exit(1)

print("\nALL SYSTEM CHECKS PASSED.")
