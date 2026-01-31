"""
Task Classifier - Classifica queries em categorias
"""

import logging
from typing import Dict, List
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TaskClassifier")


class TaskClassifier:
    """
    Classifica queries de usuário em categorias de tarefa
    """

    def __init__(self):
        """Inicializa classificador com keywords por categoria"""
        self.categories = {
            'coding': {
                'keywords': [
                    'código', 'code', 'function', 'função', 'classe', 'class',
                    'def', 'import', 'var', 'const', 'let', 'loop', 'while',
                    'for', 'api', 'http', 'python', 'javascript', 'typescript',
                    'java', 'c++', 'html', 'css', 'debug', 'error', 'fix',
                    'implement', 'django', 'fastapi', 'flask'
                ],
                'patterns': [
                    r'(write|escreva|crie)\s+(um|uma|a|an)?\s*(function|class|script|code)',
                    r'how\s+to\s+(write|code|implement)',
                    r'```(python|js|java|bash)',
                ]
            },
            'shell': {
                'keywords': [
                    'command', 'comando', 'bash', 'shell', 'terminal', 'exec',
                    'script', 'directory', 'folder', 'list', 'listar',
                    'ls', 'cd', 'mkdir', 'rm', 'cp', 'mv', 'chmod', 'sudo',
                    'grep', 'find', 'awk', 'sed', 'curl', 'ssh', 'git'
                ],
                'patterns': [
                    r'how\s+to\s+(run|execute)',
                    r'command\s+to',
                    r'install\s+package'
                ]
            },
            'reasoning': {
                'keywords': [
                    'explain', 'explicar', 'why', 'por que', 'because',
                    'porque', 'logic', 'lógica', 'reason', 'razão',
                    'step by step', 'passo a passo', 'compare', 'comparar',
                    'best practice', 'melhor prática', 'analyze', 'analisar',
                    'math', 'matemática', 'calculate', 'calcular', 'solve',
                    'resolver', 'puzzle', 'enigma', 'thought chain'
                ],
                'patterns': [
                    r'(explain|explicar)\s+(the\s+)?(logic|reason)',
                    r'step\s+by\s+step',
                    r'what\s+is\s+the\s+difference',
                    r'solve\s+this'
                ]
            },
            'general': {
                'keywords': [
                    'hello', 'olá', 'hi', 'oi', 'help', 'ajuda', 'thanks',
                    'obrigado', 'bye', 'tchau', 'who are you', 'quem é você'
                ],
                'patterns': []
            }
        }

        logger.info("✅ Task Classifier inicializado")

    def classify(self, query: str) -> str:
        """
        Classifica uma query em uma categoria
        """
        query_lower = query.lower()
        scores = {}
        for category, rules in self.categories.items():
            score = 0
            for keyword in rules['keywords']:
                if keyword in query_lower:
                    score += 1
            for pattern in rules['patterns']:
                if re.search(pattern, query_lower):
                    score += 2
            scores[category] = score
        if max(scores.values()) == 0:
            return 'general'
        best_category = max(scores, key=scores.get)
        logger.info(
            f"📊 Query classificada como: {best_category} "
            f"(score: {scores[best_category]})")
        return best_category

    def get_confidence(self, query: str) -> Dict[str, float]:
        """
        Retorna scores de confiança para todas as categorias
        """
        query_lower = query.lower()
        scores = {}
        for category, rules in self.categories.items():
            score = 0
            for keyword in rules['keywords']:
                if keyword in query_lower:
                    score += 1
            for pattern in rules['patterns']:
                if re.search(pattern, query_lower):
                    score += 2
            scores[category] = score
        total = sum(scores.values())
        if total == 0:
            return {cat: 0.25 for cat in scores}
        return {cat: score / total for cat, score in scores.items()}


_classifier = None


def get_classifier() -> TaskClassifier:
    """Retorna instância singleton do classifier"""
    global _classifier
    if _classifier is None:
        _classifier = TaskClassifier()
    return _classifier


if __name__ == "__main__":
    print("🧪 Testando Task Classifier...")
    classifier = TaskClassifier()
    tests = [
        ("Escreva uma função para calcular fibonacci", "coding"),
        ("Como listar arquivos no Linux?", "shell"),
        ("Por que usar TypeScript em vez de JavaScript?", "reasoning"),
        ("Olá, como você está?", "general"),
        ("Criar um script bash para backup", "shell"),
        ("Implementar algoritmo de ordenação", "coding")
    ]
    print("\n" + "=" * 60)
    for query, expected in tests:
        result = classifier.classify(query)
        confidence = classifier.get_confidence(query)
        status = "✅" if result == expected else "❌"
        print(f"\n{status} Query: {query}")
        print(f"   Esperado: {expected} | Resultado: {result}")
        print(f"   Confiança: {confidence[result]:.2f}")
    print("\n" + "=" * 60)
    print("✅ Testes concluídos!")