
from core.graph.supervisor import supervisor_app
from langchain_core.messages import HumanMessage
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test():
    print("🚀 Iniciando Teste do Supervisor Multi-Agente...")
    print("=" * 60)

    # Complex query that might require both research and coding (or at least
    # one specific agent)
    query = "Pesquise qual é a versão atual do Python e escreva um script hello world imprimindo essa versão."

    print(f"👤 User: {query}")
    print("=" * 60)

    inputs = {
        "messages": [HumanMessage(content=query)]
    }

    # Decrease recursion limit for safety during test
    config = {"recursion_limit": 15}

    try:
        for output in supervisor_app.stream(inputs, config=config):
            for key, value in output.items():
                print(f"\n🟢 Node Output: {key}")

                if "next" in value:
                    print(f"   👉 Decisão do Supervisor: {value['next']}")

                if "messages" in value:
                    last_msg = value["messages"][-1]
                    print(f"   🤖 {last_msg.name}: {last_msg.content[:150]}...")
                    if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                        print(
                            f"      🛠️ Tool Calls: {[tc['name'] for tc in last_msg.tool_calls]}")

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test()
