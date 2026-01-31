from core.agent.graph import build_agent
import sys


def test_sherlock():
    print("Building agent...")
    app = build_agent()

    query = "Sherlock holloway"
    print(f"Testing query: '{query}'")

    inputs = {"question": query, "chat_history": []}

    print("Invoking graph...")
    result = app.invoke(inputs)

    print("\n--- FINAL RESULT ---")
    print(result.get("generation"))

    docs = result.get("documents", [])
    print(f"\n--- DOCUMENTS ({len(docs)}) ---")
    for d in docs:
        print(d[:500] + "..." if len(d) > 500 else d)


if __name__ == "__main__":
    test_sherlock()
