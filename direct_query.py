from core.agent.graph import build_agent
import sys
import os

# Add project root to python path
sys.path.append(os.getcwd())


def main():
    print("--- Building Agent ---")
    app = build_agent()

    question = "qual o valor do dolar hoje"
    print(f"--- Asking Ziva: '{question}' ---")

    # Run the graph
    # We use a dummy thread_id for checkpointer if needed, but here we run
    # stateless if possible or just standard invoke
    config = {"configurable": {"thread_id": "test_query_1"}}

    inputs = {"question": question}

    # Stream the output to see steps
    last_generation = ""
    for output in app.stream(inputs, config=config):
        for key, value in output.items():
            print(f"Node: {key}")
            if "generation" in value:
                last_generation = value["generation"]
            if "documents" in value:
                print(f"  Docs found: {len(value['documents'])}")

    print("\n--- Final Answer ---")
    print(last_generation)


if __name__ == "__main__":
    main()
