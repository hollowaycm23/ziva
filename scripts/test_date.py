from core.agent.graph import build_agent
import sys
import os

# Adds project root to python path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_date_awareness():
    print("🚀 Ziva Date Awareness Test")
    print("Query: Que dia é hoje?")

    app = build_agent()
    state = {"question": "Que dia é hoje?", "retry_count": 0}

    for output in app.stream(state):
        for key, value in output.items():
            print(f"---{key.upper()}---")
            if key == "generate":
                print("\n╭── Answer ──╮")
                print(value["generation"])
                print("╰────────────╯")


if __name__ == "__main__":
    test_date_awareness()
