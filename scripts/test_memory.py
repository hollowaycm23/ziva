from core.agent.graph import build_agent
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_memory():
    print("🚀 Ziva Memory Test")
    app = build_agent()

    chat_history = []

    # Turn 1
    q1 = "Who is the CEO of SpaceX?"
    print(f"\nUser: {q1}")
    state1 = {
        "question": q1,
        "documents": [],
        "generation": "",
        "chat_history": chat_history}

    response1 = ""
    for output in app.stream(state1):
        if "generate" in output:
            response1 = output["generate"]["generation"]

    print(f"AI: {response1}")
    chat_history.append(f"Human: {q1}")
    chat_history.append(f"AI: {response1}")

    # Turn 2 (Contextual)
    q2 = "And does he own X?"
    print(f"\nUser: {q2}")
    state2 = {
        "question": q2,
        "documents": [],
        "generation": "",
        "chat_history": chat_history}

    for output in app.stream(state2):
        for key, value in output.items():
            if key == "contextualize_query":
                print(
                    f"  [Contextualizer] Rewritten Question: {
                        value['question']}")
            if key == "generate":
                print(f"AI: {value['generation']}")


if __name__ == "__main__":
    test_memory()
