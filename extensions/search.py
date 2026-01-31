import logging
from agent.tools import ziva_tool
# Import unified search logic
# Note: We import inside function or globally?
# To avoid circular imports if any, but unified_search is independent.
from extensions.unified_search import unified_web_search

logger = logging.getLogger("SearchTool")


@ziva_tool
def web_search(query: str) -> str:
    """
    Realiza uma busca na web inteligente (multi-fonte).
    Utiliza Wikipedia, SearxNG, Brave e outras fontes para garantir resultados.

    Args:
        query (str): Termo de busca.

    Returns:
        str: Resultados formatados em markdown.
    """
    try:
        # Delegate to the robust unified_web_search
        results_dict = unified_web_search(query, max_results=5)
        
        # Format the output string expected by the LLM
        if not results_dict:
             return "Nenhum resultado encontrado."
             
        output = f"Resultados para '{query}':\n\n"
        
        # Unified search returns a dict usually, but let's check its return type in unified_search.py
        # Logged output said: "Resultados para ... - **[Title]..."
        # Wait, unified_web_search returns a Dict according to signature, 
        # but internal implementation formats markdown string?
        # Let's check unified_search.py implementation or assume it returns Dict and we format.
        # Actually, let's look at unified_search.py again to be sure what it returns.
        # But for now, assuming it returns Dict with 'results' list or similar is risky without checking.
        # Previous log 'unified_web_search' call from fast_rag.py worked.
        # Let's check fast_rag.py usage.
        # fast_rag.py uses: results = unified_web_search(query) -> Returns Dict.
        # format_search_results(results['results'])
        
        if "results" in results_dict:
            for res in results_dict["results"]:
                title = res.get("title", "Sem título")
                url = res.get("url", "#")
                content = res.get("description", res.get("snippet", "Sem descrição"))
                output += f"- **[{title}]({url})**\n  {content}\n\n"
        
        if "deep_context" in results_dict:
            output += f"\n### CONTEÚDO EXTRAÍDO (PLAYWRIGHT):\n{results_dict['deep_context']}\n"
            
        elif "error" in results_dict:
            return f"Erro na busca: {results_dict['error']}"
            
        return output

    except Exception as e:
        logger.error(f"Erro ao buscar: {e}")
        return f"Erro ao realizar busca: {e}"
