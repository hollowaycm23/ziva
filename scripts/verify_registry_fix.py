from tools.registry.tool_registry import ToolRegistry
import time


def test_registry_fix():
    print("Testing ToolRegistry fix...")
    registry = ToolRegistry(min_time_between_creations_seconds=1)

    # 1. Register a tool
    success = registry.register_tool(
        name="test_tool_fix",
        code="def test(): pass",
        description="Test description",
        input_schema={},
        output_schema={}
    )
    print(f"First registration: {success}")

    # 2. Register SAME tool immediately (should pass due to idempotency fix)
    success_2 = registry.register_tool(
        name="test_tool_fix",
        code="def test(): pass",
        description="Test description",
        input_schema={},
        output_schema={}
    )
    print(f"Second registration (immediate): {success_2}")

    if success and success_2:
        print("SUCCESS: Registry allows idempotent registration.")
    else:
        print("FAILED: Registry blocked registration.")


if __name__ == "__main__":
    test_registry_fix()
