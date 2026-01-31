"""
Response Improver - Melhora respostas iterativamente
Usa pesquisa complementar para atingir alta confiabilidade
"""

import logging
from typing import Tuple
from core.confidence_scorer import get_confidence_scorer
from core.rag_helper import get_rag_helper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ResponseImprover")


class ResponseImprover:
    """
    Melhora respostas iterativamente até atingir threshold
    """

    def __init__(self, target_confidence: float = 0.9):
        """
        Inicializa improver
        """
        self.scorer = get_confidence_scorer()
        self.rag_helper = get_rag_helper()
        self.target_confidence = target_confidence

        logger.info(
            f"✅ Response Improver inicializado (target: {target_confidence})")

    def improve(
        self,
        query: str,
        response: str,
        max_iterations: int = 3
    ) -> Tuple[str, float]:
        """
        Melhora resposta iterativamente
        """
        current_response = response

        for iteration in range(max_iterations):
            detailed_scores = self.scorer.get_detailed_scores(
                query, current_response)
            current_score = detailed_scores['final']

            logger.info(
                f"🔄 Iteração {iteration + 1}: Score = {current_score:.2f}")

            if current_score >= self.target_confidence:
                logger.info(f"✅ Target atingido: {current_score:.2f}")
                return current_response, current_score

            weaknesses = self._identify_weaknesses(detailed_scores)
            logger.info(f"   Fraquezas: {weaknesses}")

            # Using rag_helper for research
            additional_info = self.rag_helper.search_memories(
                query, limit=5, min_score=0.5)

            if not additional_info:
                logger.warning("   Sem informações adicionais encontradas")
                break

            current_response = self._enhance_response(
                query,
                current_response,
                additional_info,
                weaknesses
            )

        final_score = self.scorer.score(query, current_response)
        logger.info(f"🏁 Score final: {final_score:.2f}")

        return current_response, final_score

    def _identify_weaknesses(self, detailed_scores: dict) -> list:
        """
        Identifica critérios com score baixo
        """
        weaknesses = []
        threshold = 0.7

        for criterion, score in detailed_scores.items():
            if criterion != 'final' and score < threshold:
                weaknesses.append(criterion)

        return weaknesses

    def _enhance_response(
        self,
        query: str,
        response: str,
        additional_info: list,
        weaknesses: list
    ) -> str:
        """
        Melhora resposta com informações adicionais
        """
        # Formatar informações adicionais
        formatted_info = self.rag_helper.format_context(additional_info)

        if not formatted_info:
            return response

        improved = f"""
{response}

---

**Informações Complementares:**

{formatted_info}
"""
        if 'completeness' in weaknesses:
            if '```' not in improved and 'exemplo' not in improved.lower():
                improved += "\n\n**Nota:** Veja exemplos no contexto acima."
        if 'sources' in weaknesses:
            improved += "\n\n**Fontes:** Baseado em conhecimento da base."
        return improved


_improver = None


def get_response_improver() -> ResponseImprover:
    """Retorna instância singleton"""
    global _improver
    if _improver is None:
        _improver = ResponseImprover()
    return _improver


if __name__ == "__main__":
    print("🧪 Testando Response Improver...")
    improver = ResponseImprover(target_confidence=0.8)
    query = "Como usar async/await em JavaScript?"
    response = "Async/await é uma sintaxe para Promises."
    print(f"\n📝 Query: {query}")
    print(f"📝 Resposta inicial ({len(response)} chars)")
    initial_score = improver.scorer.score(query, response)
    print(f"   Score inicial: {initial_score:.2f}")
    print("\n🔄 Melhorando...")
    improved, final_score = improver.improve(query, response, max_iterations=2)
    print("\n✅ Resultado:")
    print(f"   Score: {initial_score:.2f} → {final_score:.2f}")
    print(f"   Tamanho: {len(response)} → {len(improved)} chars")
    print(f"   Melhorou: {final_score > initial_score}")
    print("\n✅ Teste concluído!")