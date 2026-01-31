"""
Quality Scorer
Avalia automaticamente a qualidade das interações
"""

import re
import logging
from typing import Dict, List
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("QualityScorer")


@dataclass
class QualityMetrics:
    """Métricas de qualidade de uma interação"""
    completeness: float  # 0-1: Resposta completa?
    correctness: float   # 0-1: Resposta correta?
    relevance: float     # 0-1: Relevante ao input?
    clarity: float       # 0-1: Clara e bem formatada?
    usefulness: float    # 0-1: Útil para treinamento?

    @property
    def overall_score(self) -> float:
        """Score geral ponderado"""
        weights = {
            'completeness': 0.25,
            'correctness': 0.30,
            'relevance': 0.20,
            'clarity': 0.15,
            'usefulness': 0.10
        }

        return (
            self.completeness * weights['completeness'] +
            self.correctness * weights['correctness'] +
            self.relevance * weights['relevance'] +
            self.clarity * weights['clarity'] +
            self.usefulness * weights['usefulness']
        )


class QualityScorer:
    """Avaliador automático de qualidade"""

    def __init__(self):
        self.min_output_length = 20
        self.max_output_length = 5000

    def score_interaction(
        self,
        user_input: str,
        assistant_output: str,
        tool_calls: List[Dict],
        success: bool,
        error_message: str = None
    ) -> float:
        """Avalia qualidade de uma interação"""

        # Se falhou, score baixo automaticamente
        if not success or error_message:
            return 0.2

        # Calcular métricas individuais
        completeness = self._score_completeness(assistant_output, tool_calls)
        correctness = self._score_correctness(
            assistant_output, tool_calls, success)
        relevance = self._score_relevance(user_input, assistant_output)
        clarity = self._score_clarity(assistant_output)
        usefulness = self._score_usefulness(
            user_input, assistant_output, tool_calls)

        metrics = QualityMetrics(
            completeness=completeness,
            correctness=correctness,
            relevance=relevance,
            clarity=clarity,
            usefulness=usefulness
        )

        return metrics.overall_score

    def _score_completeness(self, output: str,
                            tool_calls: List[Dict]) -> float:
        """Avalia se a resposta está completa"""
        score = 0.5  # Base score

        # Resposta tem tamanho adequado?
        if len(output) >= self.min_output_length:
            score += 0.2

        # Resposta não está truncada?
        if not output.endswith('...') and len(output) < self.max_output_length:
            score += 0.2

        # Usou ferramentas quando apropriado?
        if tool_calls:
            score += 0.1

        return min(score, 1.0)

    def _score_correctness(
            self, output: str, tool_calls: List[Dict], success: bool) -> float:
        """Avalia correção da resposta"""
        score = 0.7 if success else 0.3

        # Não tem palavras de erro/desculpa?
        error_patterns = [
            r'desculp', r'sorry', r'erro', r'error',
            r'não consigo', r'cannot', r'unable',
            r'não sei', r"don't know"
        ]

        has_errors = any(re.search(pattern, output.lower())
                         for pattern in error_patterns)
        if not has_errors:
            score += 0.2

        # Ferramentas executaram com sucesso?
        if tool_calls and all(tc.get('success', True) for tc in tool_calls):
            score += 0.1

        return min(score, 1.0)

    def _score_relevance(self, user_input: str, output: str) -> float:
        """Avalia relevância da resposta"""
        score = 0.5

        # Extrai palavras-chave do input
        input_words = set(re.findall(r'\w+', user_input.lower()))
        output_words = set(re.findall(r'\w+', output.lower()))

        # Remove stop words comuns
        stop_words = {
            'o',
            'a',
            'de',
            'para',
            'com',
            'em',
            'the',
            'a',
            'to',
            'for',
            'of'}
        input_words -= stop_words
        output_words -= stop_words

        # Calcula overlap
        if input_words:
            overlap = len(input_words & output_words) / len(input_words)
            score += overlap * 0.5

        return min(score, 1.0)

    def _score_clarity(self, output: str) -> float:
        """Avalia clareza e formatação"""
        score = 0.5

        # Tem formatação (código, listas, etc)?
        has_code = '```' in output or '`' in output
        has_lists = re.search(r'^\s*[-*\d]+\.?\s', output, re.MULTILINE)

        if has_code:
            score += 0.2
        if has_lists:
            score += 0.1

        # Não é muito longo nem muito curto?
        if self.min_output_length <= len(output) <= self.max_output_length:
            score += 0.2

        return min(score, 1.0)

    def _score_usefulness(self, user_input: str, output: str,
                          tool_calls: List[Dict]) -> float:
        """Avalia utilidade para treinamento"""
        score = 0.5

        # Contém exemplos práticos?
        has_examples = bool(
            re.search(
                r'exemplo|example|por exemplo|for example',
                output.lower()))
        if has_examples:
            score += 0.2

        # Contém código/comandos?
        has_code = '```' in output or '`' in output
        if has_code:
            score += 0.2

        # É uma interação técnica (mais valiosa)?
        technical_keywords = [
            'código', 'code', 'comando', 'command', 'script',
            'função', 'function', 'classe', 'class', 'api'
        ]
        is_technical = any(kw in user_input.lower()
                           for kw in technical_keywords)
        if is_technical:
            score += 0.1

        return min(score, 1.0)

    def batch_score(self, interactions: List[Dict]) -> List[tuple]:
        """Avalia múltiplas interações"""
        results = []

        for interaction in interactions:
            score = self.score_interaction(
                user_input=interaction['user_input'],
                assistant_output=interaction['assistant_output'],
                tool_calls=interaction.get('tool_calls', []),
                success=interaction.get('success', True),
                error_message=interaction.get('error_message')
            )

            results.append((interaction['id'], score))

        return results


if __name__ == "__main__":
    # Teste do scorer
    scorer = QualityScorer()

    # Exemplo 1: Boa interação
    score1 = scorer.score_interaction(
        user_input="Como listar arquivos no Linux?",
        assistant_output="""Para listar arquivos no Linux, use o comando `ls`:

```bash
ls -la
```

Opções úteis:
- `-l`: formato longo
- `-a`: mostra arquivos ocultos
- `-h`: tamanhos legíveis

Exemplo:
```bash
ls -lah /home/user
```
""",
        tool_calls=[],
        success=True
    )

    print(f"✅ Boa interação: {score1:.2f}")

    # Exemplo 2: Interação ruim
    score2 = scorer.score_interaction(
        user_input="Como fazer X?",
        assistant_output="Desculpe, não sei.",
        tool_calls=[],
        success=False,
        error_message="Unknown command"
    )

    print(f"❌ Interação ruim: {score2:.2f}")

    # Exemplo 3: Interação média
    score3 = scorer.score_interaction(
        user_input="O que é Python?",
        assistant_output="Python é uma linguagem de programação.",
        tool_calls=[],
        success=True
    )

    print(f"⚠️  Interação média: {score3:.2f}")
