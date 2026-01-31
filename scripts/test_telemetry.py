
from core.agent.nodes import web_search
from core.agent.state import AgentState
import os
import json

def test_telemetry():
    print("Testing Telemetry Integration...")
    
    # Mock State
    state = {
        "question": "latest developments in quantum computing",
        "chat_history": [],
        "documents": [],
        "retry_count": 0
    }
    
    # Ensure log file is clean or we can just append
    log_file = "/home/holloway/ziva/logs/telemetry.jsonl"
    current_lines = 0
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            current_lines = len(f.readlines())
            
    # Run Web Search (this calls TelemetryManager)
    print("Invoking web_search node...")
    try:
        result = web_search(state)
        print("Web search returned.")
    except Exception as e:
        print(f"Web search failed (expected if network down, but telemetry should still log error): {e}")

    # Verify Log
    print("Verifying log file...")
    if not os.path.exists(log_file):
        print("❌ Log file not found!")
        return

    with open(log_file, "r") as f:
        lines = f.readlines()
        
    if len(lines) > current_lines:
        last_line = lines[-1]
        data = json.loads(last_line)
        print(f"✅ Telemetry Logged: {json.dumps(data, indent=2)}")
        
        if data["tool_name"] == "web_search":
            print("✅ Tool Name Correct")
        else:
            print("❌ Tool Name Mismatch")
    else:
        print("❌ No new logs found.")

if __name__ == "__main__":
    test_telemetry()
