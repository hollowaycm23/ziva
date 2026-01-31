"""
Model Selector - Selecionador Inteligente de Modelos
"""

import logging
from core.model_manager import get_model_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ModelSelector")


class ModelSelector:
    """
    Seleciona o melhor modelo LLM para a tarefa.
    """

    MODEL_MAP = {
        "coding": ["qwen2.5-coder:7b", "deepseek-coder:6.7b",
                   "ziva-base:latest"],
        "reasoning": ["deepseek-r1:8b", "deepseek-llm:7b", "llama3:8b"],
        "shell": ["qwen2.5-coder:7b", "ziva-base:latest"],
        "creative": ["llama3:8b", "mistral:7b"],
        "general": ["llama3:8b", "mistral:7b", "ziva-base:latest"]}

    def __init__(self):
        self.manager = get_model_manager()
        self.available_models = set(
            m.name for m in self.manager.list_models())
        logger.info(
            f"✅ Model Selector. Modelos: {len(self.available_models)}")

    def select_model(self, task_type: str, complexity: str = "medium") -> str:
        """
        Recebe o tipo de tarefa e retorna o nome do modelo.
        """
        candidates = self.MODEL_MAP.get(task_type, self.MODEL_MAP["general"])
        selected_model = None
        for model in candidates:
            if model in self.available_models:
                selected_model = model
                break
        if not selected_model:
            logger.warning(
                f"⚠️ Nenhum modelo ideal para '{task_type}'. Usando fallback.")
            selected_model = self._get_fallback_model()
        logger.info(f"🧠 Tarefa: {task_type} -> Modelo: {selected_model}")
        return selected_model

    def _get_fallback_model(self) -> str:
        """Retorna um modelo seguro que garantimos ter"""
        priority = ["ziva-base:latest", "mistral:7b", "qwen2.5-coder:7b"]
        for m in priority:
            if m in self.available_models:
                return m
        if self.available_models:
            return list(self.available_models)[0]
        return "ziva-base:latest"

    def refresh_models(self):
        """Atualiza a lista de modelos disponíveis"""
        self.available_models = set(
            m.name for m in self.manager.list_models())


_selector = None


def get_model_selector() -> ModelSelector:
    global _selector
    if _selector is None:
        _selector = ModelSelector()
    return _selector


if __name__ == "__main__":
    print("🎭 Testando Model Selector...")
    selector = ModelSelector()
    tasks = ["coding", "reasoning", "general", "unknown"]
    for t in tasks:
        m = selector.select_model(t)
        print(f"   Tarefas '{t}' -> {m}")