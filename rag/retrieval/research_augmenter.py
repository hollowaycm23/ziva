"""
Research Augmenter - Busca informações complementares
Melhora respostas com pesquisa adicional
"""

import logging
from typing import Dict, List
from core.rag_helper import get_rag_helper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ResearchAugmenter")


class ResearchAugmenter:
    """
    Busca informações complementares para melhorar respostas
    """

    def __init__(self):
        """Inicializa augmenter"""
        self.rag = get_rag_helper()
        logger.info("✅ Research Augmenter inicializado")

    def research(self, query: str, weaknesses: List[str]) -> Dict:
        """
        Busca informações complementares baseado em fraquezas

        Args:
            query: Pergunta original
            weaknesses: Lista de critérios fracos

        Returns:
            Dict com informações adicionais
        """
        additional_info = {}

        try:
            # RAG - sempre buscar mais contexto
            if 'completeness' in weaknesses or 'accuracy' in weaknesses:
                logger.info("🔍 Buscando mais contexto no RAG...")
                memories = self.rag.search_memories(
                    query,
                    limit=5,
                    min_score=0.4  # Mais permissivo
                )

                if memories:
                    additional_info['rag'] = {
                        'count': len(memories),
                        'context': self.rag.format_context(
                            memories,
                            max_length=800)}
                    logger.info(f"   Encontradas {len(memories)} memórias adicionais")

            # Kiwix (Offline Knowledge)
            if 'accuracy' in weaknesses or 'sources' in weaknesses:
                logger.info("📚 Buscando no Kiwix (Offline)...")
                kiwix_results = self.search_kiwix(query)
                if kiwix_results:
                    additional_info['kiwix'] = {
                        'count': len(kiwix_results),
                        'context': kiwix_results
                    }

            # Buscar variações da query
            if 'relevance' in weaknesses:
                logger.info("🔍 Buscando variações da query...")
                variations = self._generate_query_variations(query)

                all_memories = []
                for variation in variations[:2]:  # Limitar a 2 variações
                    memories = self.rag.search_memories(variation, limit=2)
                    all_memories.extend(memories)

                if all_memories:
                    additional_info['variations'] = {
                        'count': len(all_memories),
                        'context': self.rag.format_context(all_memories[:3])
                    }

            # Sugerir fontes (placeholder)
            if 'sources' in weaknesses:
                # Usar connector de busca
                try:
                    from extensions.search_connector import get_search_connector
                    search = get_search_connector()

                    if search.searxng_ok:
                        logger.info("🔍 Buscando fontes externas...")
                        web_results = search.search_web(query, limit=3)

                        if web_results:
                            formatted_sources = "\n".join(
                                [f"- [{r.title}]({r.url}): {r.snippet[:150]}..." for r in web_results]
                            )
                            additional_info['web_sources'] = formatted_sources
                            logger.info(f"   Fontes encontradas: {len(web_results)}")
                    else:
                        additional_info['sources_needed'] = True
                except ImportError:
                    logger.warning("Search connector extension not found.")
                    additional_info['sources_needed'] = True

        except Exception as e:
            logger.error(f"Erro ao pesquisar: {e}")
            # Fallback seguro
            if 'sources' in weaknesses:
                additional_info['sources_needed'] = True

        return additional_info

    def search_kiwix(self, query: str) -> str:
        """
        Busca no Kiwix local (port 8081).
        Retorna snippets formatados.
        """
        try:
            import requests
            # Assume Kiwix running at localhost:8081
            # Standard kiwix-serve search endpoint might vary based on setup (usually /search?pattern=...)
            # For this implementation, we try a common pattern.
            resp = requests.get(
                "http://localhost:8081/search",
                params={
                    "pattern": query,
                    "content": "wikipedia_en_all_maxi"},
                timeout=2)

            # Note: Parsing HTML from kiwix-serve is messy without an API.
            # If standard kiwix-serve is used, it returns HTML. Use a simple text extraction for now or assume API mode if enabled.
            # Ideally we would parse the HTML or use the OPDS feed.
            # Simplified for prototype:

            if resp.status_code == 200:
                # Placeholder: In real implementation, parse the HTML result
                # list
                return f"[Kiwix Search for '{query}' - Status 200 - OK]"
            return ""
        except ImportError:
            logger.error("Requests module missing for Kiwix search")
            return ""
        except Exception as e:
            logger.debug(f"Kiwix search failed: {e}")
            return ""

    def _generate_query_variations(self, query: str) -> List[str]:
        """
        Gera variações da query para busca mais ampla

        Args:
            query: Query original

        Returns:
            Lista de variações
        """
        variations = []

        # Variação 1: Adicionar "explicar"
        if 'como' in query.lower():
            variations.append(query.replace('Como', 'Explicar como'))

        # Variação 2: Adicionar "exemplo"
        variations.append(f"{query} exemplo")

        # Variação 3: Simplificar
        words = query.split()
        if len(words) > 3:
            variations.append(' '.join(words[:3]))

        return variations

    def format_additional_info(self, additional_info: Dict) -> str:
        """
        Formata informações adicionais para prompt

        Args:
            additional_info: Dict com informações

        Returns:
            String formatada
        """
        if not additional_info:
            return ""

        parts = []

        # RAG context
        if 'rag' in additional_info:
            rag_info = additional_info['rag']
            parts.append(f"Contexto adicional ({rag_info['count']} fontes):")
            parts.append(rag_info['context'])

        # Variations
        if 'variations' in additional_info:
            var_info = additional_info['variations']
            parts.append(f"\nInformações relacionadas ({var_info['count']} fontes):")
            parts.append(var_info['context'])

        # Sources needed
        if additional_info.get('sources_needed'):
            parts.append("\n[Nota: Adicionar referências/fontes se possível]")

        return '\n\n'.join(parts)


# Singleton
_augmenter = None


def get_research_augmenter() -> ResearchAugmenter:
    """Retorna instância singleton"""
    global _augmenter
    if _augmenter is None:
        _augmenter = ResearchAugmenter()
    return _augmenter


# Teste
if __name__ == "__main__":
    print("🧪 Testando Research Augmenter...")

    augmenter = ResearchAugmenter()

    # Teste 1: Buscar informações
    print("\n1️⃣ Buscando informações complementares...")
    query = "Como usar async/await em JavaScript?"
    weaknesses = ['completeness', 'sources']

    info = augmenter.research(query, weaknesses)
    print(f"   Informações encontradas: {list(info.keys())}")

    if info:
        formatted = augmenter.format_additional_info(info)
        print(f"\n   Formatado ({len(formatted)} chars):")
        print(f"   {formatted[:200]}...")

    print("\n✅ Teste concluído!")
