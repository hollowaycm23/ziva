import os
import sys
from unittest.mock import MagicMock, patch

# Configurar PYTHONPATH
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_ROOT)

# Mock LLM and other heavy stuff before importing analyze_node
with patch('langchain_openai.ChatOpenAI'), \
     patch('langchain_ollama.ChatOllama'), \
     patch('rag.retrieval.research_augmenter.get_research_augmenter'), \
     patch('core.reranker.get_reranker'):
    
    from core.graph.ziva_graph import analyze_node
    from langchain_core.messages import AIMessage

def test_finance_heuristic_isolated():
    print("🧪 Testando Heurística Financeira (Isolada)...")
    
    state = {
        "input": "Qual o valor do dólar agora?",
        "messages": [],
        "rag_context": "Contexto mock",
        "retry_count": 0
    }
    
    # Mock do retorno do LLM (simulando que ele não detectou ferramenta)
    mock_ai_response = MagicMock(spec=AIMessage)
    mock_ai_response.content = "O valor do dólar é flutuante."
    mock_ai_response.tool_calls = []
    
    with patch('core.graph.ziva_graph.llm.invoke', return_value=MagicMock(content="[YES]")), \
         patch('core.graph.ziva_graph.tool_llm.bind_tools') as mock_bind:
        
        # Mock bind_tools para retornar um objeto cujo invoke retorna nossa mock_ai_response
        mock_llm_with_tools = MagicMock()
        mock_llm_with_tools.invoke.return_value = mock_ai_response
        mock_bind.return_value = mock_llm_with_tools
        
        # Executar o nó de análise
        result = analyze_node(state)
        
        messages = result.get("messages", [])
        if messages:
            last_msg = messages[-1]
            if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                tool_name = last_msg.tool_calls[0]['name']
                print(f"✅ Ferramenta detectada (Heurística): {tool_name}")
                if tool_name == "unified_web_search":
                    print("🚀 TESTE PASSOU: Heurística financeira funcionou corretamente!")
                else:
                    print(f"❌ Erro: Ferramenta errada detectada: {tool_name}")
            else:
                print("❌ FALHA: Nenhuma ferramenta detectada pela heurística.")
        else:
            print("❌ FALHA: Nenhuma mensagem retornada.")

if __name__ == "__main__":
    test_finance_heuristic_isolated()
