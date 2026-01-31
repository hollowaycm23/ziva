from core.agent.graph import build_agent
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_agent():
    print("🚀 Initializing Agent...")
    app = build_agent()

    question = "qual a arquetetura da ziva"
    print(f"\n❓ Asking: {question}")

    # Initial State
    initial_state = {"question": question, "documents": [], "generation": ""}

    # Run Graph
    for output in app.stream(initial_state):
        for key, value in output.items():
            print(f"  📍 Node '{key}': processed.")

    print("\n✅ Flow Completed!")


if __name__ == "__main__":
    test_agent()
