import os
import sys

# Configurar PYTHONPATH
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_ROOT)

from core.graph.ziva_graph import analyze_node
from langchain_core.messages import HumanMessage, AIMessage

def test_finance_heuristic():
    print("🧪 Testando Heurística Financeira...")
    
    state = {
        "input": "Como está a variação do dólar hoje e com o que está correlacionada?",
        "messages": [],
        "rag_context": "",
        "retry_count": 0
    }
    
    # Executar o nó de análise
    result = analyze_node(state)
    
    print(f"Análise: {result.get('analysis')}")
    print(f"Ferramenta necessária: {result.get('tool_needed')}")
    
    messages = result.get("messages", [])
    if messages:
        last_msg = messages[-1]
        if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
            print(f"✅ Ferramenta detectada: {last_msg.tool_calls[0]['name']}")
            print(f"✅ Query detectada: {last_msg.tool_calls[0]['args']['query']}")
        else:
            print("❌ Nenhuma ferramenta detectada via tool_calls.")
    else:
        print("❌ Nenhuma mensagem retornada.")

if __name__ == "__main__":
    # Mocking LLM failure or specific behavior if needed by env vars
    os.environ["ZIVA_LLM_BACKEND"] = "lm_studio"
    test_finance_heuristic()
