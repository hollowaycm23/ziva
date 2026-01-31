"""
Adapter Router - Seleciona e gerencia adapters LoRA
Roteia queries para o adapter mais apropriado
"""

import logging
import json
from pathlib import Path
from typing import Optional, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AdapterRouter")


class AdapterRouter:
    """
    Gerencia routing de queries para adapters LoRA apropriados
    Mantém cache de adapters carregados
    """

    def __init__(
            self,
            registry_path: str = "/home/holloway/ziva/adapters/registry.json"):
        """
        Inicializa router com registry de adapters

        Args:
            registry_path: Caminho para arquivo de configuração
        """
        self.registry_path = Path(registry_path)
        self.registry = self._load_registry()
        self.loaded_adapters = {}
        self.base_model = self.registry.get('base_model', 'qwen2.5-coder:7b')

        logger.info("✅ Adapter Router inicializado")
        logger.info(f"   Base model: {self.base_model}")
        logger.info(
            f"   Adapters disponíveis: {len(self.registry['adapters'])}"
        )

    def _load_registry(self) -> Dict:
        """Carrega registry de adapters do arquivo JSON"""
        try:
            with open(self.registry_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Registry não encontrado: {self.registry_path}")
            return {
                'adapters': {},
                'base_model': 'qwen2.5-coder:7b',
                'fallback_strategy': 'base_model'
            }

    def get_adapter_info(self, task_type: str) -> Optional[Dict]:
        """
        Retorna informações sobre adapter para tipo de tarefa

        Args:
            task_type: Tipo de tarefa (coding, shell, etc)

        Returns:
            Dict com info do adapter ou None
        """
        return self.registry['adapters'].get(task_type)

    def get_model_name(self, task_type: str) -> str:
        """
        Retorna nome do modelo para usar

        Args:
            task_type: Tipo de tarefa

        Returns:
            Nome do modelo (com ou sem adapter)
        """
        adapter_info = self.get_adapter_info(task_type)

        if not adapter_info:
            logger.info(f"📌 Usando base model para: {task_type}")
            return self.base_model

        if adapter_info.get('path'):
            adapter_path = adapter_info['path']
            if Path(adapter_path).exists():
                logger.info(f"🎯 Usando adapter para: {task_type}")
                return f"{adapter_info['model']}+{adapter_path}"

        logger.info(f"📌 Fallback para base model: {task_type}")
        return adapter_info.get('model', self.base_model)

    def should_use_adapter(self, task_type: str) -> bool:
        """
        Verifica se deve usar adapter para tipo de tarefa

        Args:
            task_type: Tipo de tarefa

        Returns:
            True se deve usar adapter
        """
        adapter_info = self.get_adapter_info(task_type)

        if not adapter_info:
            return False

        adapter_path = adapter_info.get('path')
        if adapter_path and Path(adapter_path).exists():
            adapter_file = Path(adapter_path) / "adapter_model.safetensors"
            return adapter_file.exists()

        return False

    def get_routing_decision(self, task_type: str) -> Dict:
        """
        Retorna decisão completa de routing

        Args:
            task_type: Tipo de tarefa

        Returns:
            Dict com decisão de routing
        """
        adapter_info = self.get_adapter_info(task_type)
        use_adapter = self.should_use_adapter(task_type)
        model_name = self.get_model_name(task_type)

        return {
            'task_type': task_type,
            'use_adapter': use_adapter,
            'model': model_name,
            'adapter_path': adapter_info.get('path') if adapter_info else None,
            'description': (
                adapter_info.get('description') if adapter_info
                else 'Base model'),
            'priority': adapter_info.get(
                'priority',
                99) if adapter_info else 99}


_router = None


def get_router() -> AdapterRouter:
    """Retorna instância singleton do router"""
    global _router
    if _router is None:
        _router = AdapterRouter()
    return _router


if __name__ == "__main__":
    print("🧪 Testando Adapter Router...")

    router = AdapterRouter()

    print("\n" + "=" * 60)
    print("📋 Registry carregado:")
    print(json.dumps(router.registry, indent=2))

    print("\n" + "=" * 60)
    print("🎯 Testando routing decisions:")

    task_types = ['coding', 'shell', 'reasoning', 'general']

    for task_type in task_types:
        decision = router.get_routing_decision(task_type)
        print(f"\n{task_type.upper()}:")
        print(f"  Use adapter: {decision['use_adapter']}")
        print(f"  Model: {decision['model']}")
        print(f"  Description: {decision['description']}")
        print(f"  Priority: {decision['priority']}")

    print("\n" + "=" * 60)
    print("✅ Testes concluídos!")
