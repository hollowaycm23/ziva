import os
import sys

# Configurar PYTHONPATH
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_ROOT)

from core.tools.searxng import SearXNGClient

def test_searxng_html():
    print("🔍 Testando SearXNG (HTML Scraping)...")
    client = SearXNGClient()
    
    # Testar com a mesma query
    results = client.search("variação do dólar hoje correlação", num_results=3)
    print(f"📊 Resultados encontrados: {len(results)}")
    for i, r in enumerate(results):
        print(f"--- Resultado {i+1} ---")
        print(f"Título: {r.get('title')}")
        print(f"URL: {r.get('url')}")
        print(f"Snippet: {r.get('snippet')[:200]}...")
    
    if len(results) > 0:
        print("🚀 TESTE PASSOU: Scraping HTML do SearXNG funcionando!")
    else:
        print("❌ FALHA: Nenhum resultado retornado via HTML Scraping.")

if __name__ == "__main__":
    test_searxng_html()
