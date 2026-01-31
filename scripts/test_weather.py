from core.agent.graph import build_agent
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_weather():
    print("🚀 Ziva Weather Tool Test")
    queries = [
        "Como está o clima em Nova York?",
        "Qual a temperatura em Paris?"]

    app = build_agent()

    for q in queries:
        print(f"\nQuery: {q}")
        state = {
            "question": q,
            "documents": [],
            "generation": "",
            "chat_history": []}

        for output in app.stream(state):
            for key, value in output.items():
                print(f"---{key.upper()}---")
                if key == "generate":
                    print("\n╭── Answer ──╮")
                    print(value["generation"])
                    print("╰────────────╯")


if __name__ == "__main__":
    test_weather()
