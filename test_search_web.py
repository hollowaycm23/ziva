import os
import sys

# Configurar PYTHONPATH
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_ROOT)

from extensions.search_connector import get_search_connector

def test_search_connector():
    print("🔍 Testando Search Connector (SearxNG)...")
    connector = get_search_connector()
    
    if connector.searxng_ok:
        print("✅ SearxNG Online")
        # Testar com uma query financeira real
        results = connector.search_web("variação do dólar hoje correlação", limit=3)
        print(f"📊 Resultados encontrados: {len(results)}")
        for i, r in enumerate(results):
            print(f"--- Resultado {i+1} ---")
            print(f"Título: {r.title}")
            print(f"URL: {r.url}")
            print(f"Snippet: {r.snippet[:200]}...")
        
        if len(results) > 0:
            print("🚀 TESTE PASSOU: Busca web funcionando!")
        else:
            print("❌ FALHA: Nenhum resultado retornado do SearxNG.")
    else:
        print("❌ FALHA: SearxNG Offline")

if __name__ == "__main__":
    test_search_connector()
