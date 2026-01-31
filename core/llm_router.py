"""
Intelligent LLM Router for Ziva.
"""

import logging
from typing import Optional, Dict, List
from dataclasses import dataclass

logger = logging.getLogger("LLMRouter")


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    name: str
    strengths: List[str]
    use_cases: List[str]
    priority: int = 5


class LLMRouter:
    """
    Routes queries to optimal LLM models based on task classification.
    """

    MODELS = {
        'annika-logic': ModelConfig(
            name='annika-logic:latest',
            strengths=['logic', 'reasoning', 'decision-making'],
            use_cases=['tool_selection', 'critical_decisions'],
            priority=9
        ),
        'qwen-coder': ModelConfig(
            name='qwen2.5-coder:7b',
            strengths=['code', 'programming', 'debugging'],
            use_cases=['code_generation', 'code_analysis', 'debugging'],
            priority=8
        ),
        'deepseek': ModelConfig(
            name='deepseek-r1:8b',
            strengths=['reasoning', 'chain-of-thought'],
            use_cases=['complex_reasoning', 'explanations', 'analysis'],
            priority=7
        ),
        'llama3': ModelConfig(
            name='llama3:8b',
            strengths=['conversation', 'general-knowledge', 'chat'],
            use_cases=['general_chat', 'knowledge_qa', 'summarization'],
            priority=6
        ),
        'ziva-base': ModelConfig(
            name='ziva-base:latest',
            strengths=['ziva-specific', 'custom-tasks'],
            use_cases=['ziva_operations', 'custom_workflows'],
            priority=7
        ),
        'mistral': ModelConfig(
            name='mistral:7b',
            strengths=['balanced', 'multi-purpose'],
            use_cases=['fallback', 'general_tasks'],
            priority=5
        )
    }

    TASK_PATTERNS = {
        'logic_decision': {'keywords': ['decide', 'should', 'choose'],
                           'model': 'annika-logic', 'confidence': 0.9},
        'tool_selection': {'keywords': ['tool', 'ferramenta', 'execute'],
                           'model': 'annika-logic', 'confidence': 0.95},
        'code': {'keywords': ['python', 'function', 'code', 'debug'],
                 'model': 'qwen-coder', 'confidence': 0.9},
        'reasoning': {'keywords': ['why', 'explain', 'porque', 'explicar'],
                      'model': 'deepseek', 'confidence': 0.8},
        'search': {'keywords': ['pesquise', 'busque', 'search', 'find'],
                   'model': 'llama3', 'confidence': 0.85},
        'conversation': {'keywords': ['hello', 'hi', 'olá', 'oi'],
                         'model': 'llama3', 'confidence': 0.9}
    }

    def __init__(self, default_model: str = 'mistral:7b'):
        self.default_model = default_model
        self.routing_stats = {}

    def classify_task(self, query: str,
                      context: Optional[str] = None) -> Dict:
        """
        Classify the task type from the query.
        """
        query_lower = query.lower()
        matches = []
        for task_type, pattern in self.TASK_PATTERNS.items():
            keyword_matches = sum(
                1 for kw in pattern['keywords'] if kw in query_lower)
            if keyword_matches > 0:
                confidence = min(
                    pattern['confidence'] * (keyword_matches /
                                             len(pattern['keywords'])), 1.0)
                matches.append({
                    'task_type': task_type,
                    'model': pattern['model'],
                    'confidence': confidence,
                    'keyword_matches': keyword_matches
                })
        matches.sort(key=lambda x: x['confidence'], reverse=True)
        if matches:
            best_match = matches[0]
            logger.info(
                f"Task classified as '{best_match['task_type']}' "
                f"with confidence {best_match['confidence']:.2f}")
            return best_match
        return {'task_type': 'general', 'model': 'mistral',
                'confidence': 0.5, 'keyword_matches': 0}

    def select_model(
            self,
            query: str,
            task_type: Optional[str] = None,
            context: Optional[str] = None) -> str:
        """
        Select the optimal model for a query.
        """
        if task_type:
            for pattern in self.TASK_PATTERNS.values():
                if (pattern.get('task_type') == task_type or
                        task_type in pattern['keywords']):
                    model_key = pattern['model']
                    model_name = self.MODELS[model_key].name
                    self._log_routing(query, model_name, task_type, 1.0)
                    return model_name
        classification = self.classify_task(query, context)
        model_key = classification['model']
        model_name = self.MODELS[model_key].name
        self._log_routing(
            query, model_name,
            classification['task_type'], classification['confidence'])
        return model_name

    def _log_routing(self, query: str, model: str,
                     task_type: str, confidence: float):
        """Log routing decision for analytics."""
        logger.info(
            f"🎯 Routed to {model} (task: {task_type}, "
            f"confidence: {confidence:.2f})")
        if model not in self.routing_stats:
            self.routing_stats[model] = {'count': 0, 'tasks': {}}
        self.routing_stats[model]['count'] += 1
        if task_type not in self.routing_stats[model]['tasks']:
            self.routing_stats[model]['tasks'][task_type] = 0
        self.routing_stats[model]['tasks'][task_type] += 1

    def get_stats(self) -> Dict:
        """Get routing statistics."""
        return self.routing_stats

    def get_model_for_node(self, node_name: str) -> str:
        """
        Get recommended model for a specific graph node.
        """
        node_models = {
            'analyze_node': 'annika-logic:latest',
            'lookup_tool_node': 'annika-logic:latest',
            'respond_node': 'llama3:8b',
            'execute_tool_node': 'qwen2.5-coder:7b',
        }
        return node_models.get(node_name, self.default_model)


_router_instance: Optional[LLMRouter] = None


def get_router() -> LLMRouter:
    """Get or create global router instance."""
    global _router_instance
    if _router_instance is None:
        _router_instance = LLMRouter()
    return _router_instance


if __name__ == "__main__":
    router = LLMRouter()
    test_queries = [
        ("pesquise sobre inteligência artificial", None),
        ("escreva uma função python para fibonacci", None),
        ("por que o céu é azul?", None),
        ("qual a melhor abordagem: A ou B?", None),
        ("olá, como você está?", None),
        ("decide if a tool is needed", "tool_selection"),
    ]
    print("🧪 Testing LLM Router\n")
    for query, task_type in test_queries:
        model = router.select_model(query, task_type)
        print(f"Query: {query[:50]}")
        print(f"Model: {model}\n")
    print("\n📊 Routing Stats:")
    import json
    print(json.dumps(router.get_stats(), indent=2))