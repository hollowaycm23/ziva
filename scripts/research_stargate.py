from core.agent.graph import build_agent
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def research_stargate():
    print("🚀 Ziva Deep Research Test: Stargate")
    query = "pesquisa profunda sobre portais e sistemas de ativacao de portal stargate e energia envolvidas ou gerador ou quantidade energia necessaria"
    print(f"Query: {query}")

    app = build_agent()
    state = {
        "question": query,
        "documents": [],
        "generation": "",
        "chat_history": []
    }

    for output in app.stream(state):
        for key, value in output.items():
            print(f"---{key.upper()}---")
            if key == "web_search":
                docs = value.get("documents", [])
                print(f"  [Web Search] Found {len(docs)} documents.")
            if key == "generate":
                print("\n╭── Answer ──╮")
                print(value["generation"])
                print("╰────────────╯")


if __name__ == "__main__":
    research_stargate()
