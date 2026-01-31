import logging
import json
from pathlib import Path
from agent.tools import ziva_tool

logger = logging.getLogger("DocumentTools")


@ziva_tool
def search_documentation(query: str, limit: int = 3) -> str:
    """
    Busca na documentação indexada (incluindo artifacts .gemini).

    Args:
        query: Termo de busca
        limit: Número máximo de resultados

    Returns:
        str: Documentos relevantes encontrados
    """
    try:
        from core.rag import RAGService

        rag = RAGService()
        results = rag.search(query, limit=limit)

        if not results:
            return "Nenhum documento encontrado."

        output = f"Documentação encontrada para '{query}':\n\n"
        for i, result in enumerate(results, 1):
            metadata = result.get('metadata', {})
            content_preview = result.get('content', '')[:200]

            output += f"{i}. **{metadata.get('filename', 'Unknown')}**\n"
            output += f"   Fonte: {metadata.get('source', 'N/A')}\n"
            output += f"   Preview: {content_preview}...\n\n"

        return output

    except Exception as e:
        logger.error(f"Erro ao buscar documentação: {e}")
        return f"Erro: {e}"
