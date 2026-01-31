"""
Confidence Scorer - Avalia confiabilidade de respostas
Score de 0-1 baseado em múltiplos critérios
"""

import logging
import re
from typing import Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ConfidenceScorer")


class ConfidenceScorer:
    """
    Avalia confiança/qualidade de respostas geradas
    Score 0-1 baseado em 5 critérios
    """

    def __init__(self):
        """Inicializa scorer com pesos configuráveis"""
        self.weights = {
            'completeness': 0.25,
            'accuracy': 0.30,
            'relevance': 0.25,
            'clarity': 0.10,
            'sources': 0.10
        }

        logger.info("✅ Confidence Scorer inicializado")

    def score(self, query: str, response: str) -> float:
        """
        Calcula score de confiança

        Args:
            query: Pergunta original
            response: Resposta gerada

        Returns:
            Score 0-1
        """
        scores = {
            'completeness': self._check_completeness(response),
            'accuracy': self._check_accuracy(query, response),
            'relevance': self._check_relevance(query, response),
            'clarity': self._check_clarity(response),
            'sources': self._check_sources(response)
        }

        final_score = sum(
            scores[criterion] * self.weights[criterion]
            for criterion in scores
        )

        logger.debug(f"📊 Scores: {scores} → Final: {final_score:.2f}")

        return final_score

    def _check_completeness(self, response: str) -> float:
        """Verifica se resposta é completa"""
        score = 0.0
        if len(response) >= 100:
            score += 0.3
        elif len(response) >= 50:
            score += 0.15
        if '```' in response or 'exemplo:' in response.lower():
            score += 0.4
        if '\n' in response and len(response.split('\n')) >= 3:
            score += 0.2
        conclusion_words = ['portanto', 'resumindo', 'conclusão', 'em resumo']
        if any(word in response.lower() for word in conclusion_words):
            score += 0.1
        return min(score, 1.0)

    def _check_accuracy(self, query: str, response: str) -> float:
        """Verifica indicadores de precisão"""
        score = 1.0
        if len(response) < 50:
            score -= 0.4
        uncertainty_words = [
            'talvez', 'acho que', 'não tenho certeza',
            'provavelmente', 'pode ser', 'não sei'
        ]
        for word in uncertainty_words:
            if word in response.lower():
                score -= 0.2
                break
        if 'mas' in response and 'porém' in response:
            score -= 0.1
        if re.search(r'\d+', response):
            score += 0.1
        return max(score, 0.0)

    def _check_relevance(self, query: str, response: str) -> float:
        """Verifica relevância para a pergunta"""
        query_lower = query.lower()
        response_lower = response.lower()
        query_words = set(re.findall(r'\w+', query_lower))
        query_words = {w for w in query_words if len(w) > 3}
        response_words = set(re.findall(r'\w+', response_lower))
        if not query_words:
            return 0.5
        overlap = len(query_words & response_words)
        relevance = min(overlap / len(query_words), 1.0)
        if response_lower.startswith(tuple(['sim', 'não', 'é', 'são'])):
            relevance += 0.2
        return min(relevance, 1.0)

    def _check_clarity(self, response: str) -> float:
        """Verifica clareza da resposta"""
        score = 0.5
        sentences = response.split('.')
        avg_length = sum(len(s) for s in sentences) / max(len(sentences), 1)
        if avg_length < 100:
            score += 0.3
        elif avg_length > 200:
            score -= 0.2
        if any(marker in response for marker in ['**', '##', '-', '•']):
            score += 0.2
        return max(min(score, 1.0), 0.0)

    def _check_sources(self, response: str) -> float:
        """Verifica se tem referências/fontes"""
        score = 0.0
        if 'http' in response or 'www.' in response:
            score += 0.4
        if '"' in response or '«' in response:
            score += 0.3
        source_words = [
            'segundo',
            'de acordo com',
            'conforme',
            'baseado em']
        if any(word in response.lower() for word in source_words):
            score += 0.3
        return min(score, 1.0)

    def get_detailed_scores(
            self, query: str, response: str) -> Dict[str, float]:
        """
        Retorna scores detalhados por critério

        Returns:
            Dict com scores individuais e final
        """
        scores = {
            'completeness': self._check_completeness(response),
            'accuracy': self._check_accuracy(query, response),
            'relevance': self._check_relevance(query, response),
            'clarity': self._check_clarity(response),
            'sources': self._check_sources(response)
        }
        scores['final'] = sum(
            scores[c] * self.weights[c] for c in self.weights
        )
        return scores


_scorer = None


def get_confidence_scorer() -> ConfidenceScorer:
    """Retorna instância singleton"""
    global _scorer
    if _scorer is None:
        _scorer = ConfidenceScorer()
    return _scorer


if __name__ == "__main__":
    print("🧪 Testando Confidence Scorer...")
    scorer = ConfidenceScorer()
    tests = [{'query': 'Como usar async/await em JavaScript?',
              'response': '''Async/await é uma sintaxe moderna para trabalhar
              com Promises em JavaScript.''',
              'expected': '>= 0.8'},
             {'query': 'O que é TypeScript?',
              'response': 'É um superset de JavaScript.',
              'expected': '< 0.6'},
             {'query': 'Qual o clima hoje?',
              'response': 'Não tenho certeza, talvez esteja ensolarado.',
              'expected': '< 0.5'}]

    print("\n" + "=" * 60)
    for i, test in enumerate(tests, 1):
        score = scorer.score(test['query'], test['response'])
        detailed = scorer.get_detailed_scores(test['query'], test['response'])
        print(f"\n{i}. Query: {test['query'][:50]}...")
        print(f"   Score: {score:.2f} (esperado: {test['expected']})")
        print("   Detalhado:")
        for criterion, value in detailed.items():
            if criterion != 'final':
                print(f"     {criterion}: {value:.2f}")
    print("\n" + "=" * 60)
    print("✅ Testes concluídos!")