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
        results_dict = unified_web_search(query, max_results=5, deep_scrape=False)

        if not results_dict:
            return "Nenhum resultado encontrado nas fontes disponíveis."

        results_list = results_dict.get("results", [])
        if not results_list:
            return f"NÃO ENCONTREI resultados para '{query}'. O termo pode estar incorreto. NÃO invente produtos ou links."

        output = f"Resultados para '{query}':\n\n"

        for res in results_list:
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
