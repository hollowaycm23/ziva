import os
import sys
from unittest.mock import MagicMock, patch

# Configurar PYTHONPATH
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_ROOT)

# Mock e importar
with patch('langchain_openai.ChatOpenAI'), \
     patch('langchain_ollama.ChatOllama'), \
     patch('rag.retrieval.research_augmenter.get_research_augmenter'), \
     patch('core.reranker.get_reranker'):
    
    from core.graph.ziva_graph import analyze_node
    from langchain_core.messages import AIMessage

def test_tech_heuristic_and_fallback():
    print("🧪 Testando Heurística Tecnológica e Fallback de Contexto...")
    
    # Caso 1: Heurística de Tecnologia (Habitat)
    state_tech = {
        "input": "quais as tecnoligias de habitat espacial?",
        "messages": [],
        "rag_context": "Algum contexto inútil",
        "retry_count": 0
    }
    
    mock_ai_response = MagicMock(spec=AIMessage)
    mock_ai_response.content = "Não sei."
    mock_ai_response.tool_calls = []
    
    with patch('core.graph.ziva_graph.llm.invoke', return_value=MagicMock(content="[YES]")), \
         patch('core.graph.ziva_graph.tool_llm.bind_tools') as mock_bind:
        
        mock_llm_with_tools = MagicMock()
        mock_llm_with_tools.invoke.return_value = mock_ai_response
        mock_bind.return_value = mock_llm_with_tools
        
        result = analyze_node(state_tech)
        last_msg = result["messages"][-1]
        
        if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
            print(f"✅ Ferramenta detectada (Tech): {last_msg.tool_calls[0]['name']}")
        else:
            print("❌ FALHA: Heurística tecnológica não disparou.")

    # Caso 2: Fallback de Contexto Inútil (Nota de fallback)
    state_fallback = {
        "input": "me diga algo novo",
        "messages": [],
        "rag_context": "\n[Nota: Adicionar referências/fontes se possível]",
        "retry_count": 0
    }
    
    with patch('core.graph.ziva_graph.llm.invoke', return_value=MagicMock(content="[YES]")), \
         patch('core.graph.ziva_graph.tool_llm.bind_tools') as mock_bind:
        
        mock_llm_with_tools = MagicMock()
        mock_llm_with_tools.invoke.return_value = mock_ai_response
        mock_bind.return_value = mock_llm_with_tools
        
        result = analyze_node(state_fallback)
        last_msg = result["messages"][-1]
        
        if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
            print(f"✅ Ferramenta detectada (Fallback): {last_msg.tool_calls[0]['name']}")
        else:
            print("❌ FALHA: Fallback de contexto inútil não disparou.")

if __name__ == "__main__":
    test_tech_heuristic_and_fallback()
