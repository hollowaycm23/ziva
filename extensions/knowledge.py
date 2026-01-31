import requests
import logging
from agent.tools import ziva_tool

logger = logging.getLogger("KnowledgeTool")


@ziva_tool
def medical_lookup(query: str) -> str:
    """
    Consulta a base de conhecimento médico offline (WikiMed) via Kiwix.

    Args:
        query (str): Termo médico ou tópico.

    Returns:
        str: Conteúdo do artigo ou erro.
    """
    # Kiwix-serve geralmente roda na 8081 para nos
    base_url = "http://localhost:8081/medicine_pt/A/"

    # Kiwix busca é um pouco diferente, geralmente se acessa o artigo direto ou via search endpoint
    # Vamos tentar o search endpoint do kiwix-serve se disponível, ou busca
    # simples
    search_url = "http://localhost:8081/search"
    params = {"q": query, "content": "medicine_pt"}

    try:
        # Tenta buscar o artigo mais relevante
        response = requests.get(search_url, params=params, timeout=5)
        if response.status_code == 200:
            # O kiwix-serve retorna HTML com os resultados.
            # Parsear HTML aqui seria complexo sem bs4.
            # Por enquanto, sugere o link direto.
            return f"Consulta para '{query}' enviada ao Kiwix. Verifique em http://localhost:8081"

        return "Serviço Kiwix indisponível."
    except Exception as e:
        return f"Erro ao acessar Kiwix: {e}"
