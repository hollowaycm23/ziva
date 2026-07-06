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
                try:
                    from extensions.search_connector import get_search_connector
                    search = get_search_connector()

                    if search.searxng_ok:
                        logger.info("🔍 Buscando fontes externas...")
                        queries = [query]
                        date_hints = ["2022", "2023", "2024", "2025", "2026"]
                        if not any(y in query for y in date_hints):
                            queries.append(f"{query} {date_hints[0]}")
                        all_results = []
                        seen_urls = set()
                        for q in queries:
                            web_results = search.search_web(q, limit=5)
                            for r in web_results:
                                if r.url not in seen_urls:
                                    seen_urls.add(r.url)
                                    all_results.append(r)

                        if all_results:
                            formatted_sources = "\n".join(
                                [f"- [{r.title}]({r.url}): {r.snippet[:500]}" for r in all_results]
                            )
                            additional_info['web_sources'] = formatted_sources
                            logger.info(f"   Fontes encontradas: {len(all_results)} (de {len(queries)} queries)")
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
            from bs4 import BeautifulSoup
            resp = requests.get(
                "http://localhost:8081/search",
                params={"pattern": query},
                timeout=5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                results = []
                for result in soup.select('.result, .article, li.result')[:5]:
                    text = result.get_text(strip=True)
                    if text and len(text) > 20:
                        results.append(text[:300])
                if results:
                    return "\n\n".join(results)
                return ""
            return ""
        except ImportError:
            logger.error("Requests or BeautifulSoup missing for Kiwix search")
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

        # Web sources
        if 'web_sources' in additional_info:
            parts.append(f"Informações web:\n{additional_info['web_sources']}")

        # Kiwix (offline knowledge)
        if 'kiwix' in additional_info:
            parts.append(f"Conhecimento offline:\n{additional_info['kiwix'].get('context', '')}")

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
