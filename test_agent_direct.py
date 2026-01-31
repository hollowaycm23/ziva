import sys
import os
from pprint import pprint

# Setup path
sys.path.append(os.getcwd())

from core.agent.graph import build_agent
from core.agent.state import AgentState

def test_direct():
    print("🚀 Building agent...")
    app = build_agent()
    
    print("🧪 Running test query...")
    initial_state = AgentState(
        question="Qual a cotação do dólar hoje?",
        chat_history=[],
        documents=[],
        generation="",
        retry_count=0,
        mode="general"
    )
    
    # Run the graph
    inputs = initial_state
    for output in app.stream(inputs):
        for key, value in output.items():
            print(f"--- Node: {key} ---")
            # pprint(value)
            if "generation" in value:
                print(f"🤖 Answer: {value['generation']}")

if __name__ == "__main__":
    test_direct()
