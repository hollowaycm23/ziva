from core.agent.graph import build_agent
import sys
import os

# Adds project root to python path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_web_search():
    print("🚀 Ziva Web Search Test")
    print("Query: What is the current price of Ethereum?")

    app = build_agent()
    state = {
        "question": "What is the current price of Ethereum?",
        "retry_count": 0}

    # We expect:
    # 1. Retrieve -> Fail (or irrelevant)
    # 2. Grade -> No
    # 3. Transform Query -> Retry
    # 4. ... Max Retries ...
    # 5. Web Search -> SearXNG -> Playwright
    # 6. Generate

    for output in app.stream(state):
        for key, value in output.items():
            print(f"---{key.upper()}---")
            if key == "generation":
                print("\n╭── Answer ──╮")
                print(value["generation"])
                print("╰────────────╯")


if __name__ == "__main__":
    test_web_search()
