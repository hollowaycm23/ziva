import sys
import os

sys.path.append(os.getcwd())

# Mock the @ziva_tool decorator if needed, or import the real one works if dependencies are met
# Assuming runtime environment is set up
from extensions.file_ops import file_reader

def test_bridge():
    print("🌉 Testing Python -> Go Bridge (Lobotomy Check)...\n")
    
    # 1. Valid Read
    target = "core/runtime/protocol.go"
    print(f"👉 Reading valid file: {target}")
    result = file_reader(target)
    if "type ToolRequest struct" in result:
        print("✅ SUCCESS: Content retrieved via Go Runtime.")
    else:
        print(f"❌ FAILURE: Unexpected content: {result[:100]}...")
        
    print("-" * 30)
        
    # 2. Invalid Read (Sandbox)
    target_bad = "/etc/passwd"
    print(f"👉 Reading FORBIDDEN file: {target_bad}")
    result_bad = file_reader(target_bad)
    if "outside sandbox" in result_bad or "Access Denied" in result_bad:
        print("✅ SUCCESS: Sandbox correctly blocked access.")
        print(f"   Message: {result_bad}")
    else:
        print(f"❌ FAILURE: Sandbox failed? Result: {result_bad[:100]}...")

if __name__ == "__main__":
    if os.getenv("ZIVA_USE_GO_RUNTIME") != "true":
         # Force it for this test just in case default changed
         os.environ["ZIVA_USE_GO_RUNTIME"] = "true"
         
    # Ensure server is running? The user/previous steps should have it running.
    # We can try to curl to check first? No, let's trust the environment.
    test_bridge()
