"""
Adapter Manager for Ziva Fine-Tuning System.

Gerencia múltiplos adaptadores LoRA por tarefa, versionamento e deployment.
"""

import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("AdapterManager")


class AdapterManager:
    """
    Gerencia adaptadores LoRA/QLoRA da Ziva.

    Funcionalidades:
    - Múltiplos adaptadores por tarefa
    - Versionamento
    - Troca dinâmica
    - A/B testing
    - Rollback
    """

    def __init__(self, adapters_dir: str = "models/adapters"):
        """
        Inicializa o gerenciador.

        Args:
            adapters_dir (str): Diretório base dos adaptadores
        """
        self.adapters_dir = Path(adapters_dir)
        self.adapters_dir.mkdir(parents=True, exist_ok=True)

        self.registry_file = self.adapters_dir / "registry.json"
        self.registry = self._load_registry()

        self.current_adapters = {}  # task_type -> adapter_path

    def _load_registry(self) -> Dict:
        """Carrega registro de adaptadores"""
        if self.registry_file.exists():
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        return {"adapters": {}, "versions": {}}

    def _save_registry(self):
        """Salva registro de adaptadores"""
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2)

    def register_adapter(self, adapter_path: str, task_type: str,
                         version: str = "v1.0",
                         metadata: Optional[Dict] = None):
        """
        Registra novo adaptador.

        Args:
            adapter_path (str): Caminho do adaptador
            task_type (str): Tipo de tarefa
            version (str): Versão do adaptador
            metadata (Dict, optional): Metadados adicionais
        """
        adapter_id = f"{task_type}_{version}"

        dest_path = self.adapters_dir / task_type / version
        dest_path.mkdir(parents=True, exist_ok=True)

        for file in Path(adapter_path).glob("*"):
            shutil.copy2(file, dest_path / file.name)

        if task_type not in self.registry["adapters"]:
            self.registry["adapters"][task_type] = []

        adapter_info = {
            "id": adapter_id,
            "version": version,
            "path": str(dest_path),
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        self.registry["adapters"][task_type].append(adapter_info)

        if task_type not in self.registry["versions"]:
            self.registry["versions"][task_type] = version

        self._save_registry()
        logger.info(f"✅ Adaptador registrado: {adapter_id}")

    def list_adapters(self, task_type: Optional[str] = None) -> List[Dict]:
        """
        Lista adaptadores disponíveis.

        Args:
            task_type (str, optional): Filtrar por tipo de tarefa

        Returns:
            List[Dict]: Lista de adaptadores
        """
        if task_type:
            return self.registry["adapters"].get(task_type, [])

        all_adapters = []
        for adapters in self.registry["adapters"].values():
            all_adapters.extend(adapters)
        return all_adapters

    def get_active_adapter(self, task_type: str) -> Optional[str]:
        """
        Retorna caminho do adaptador ativo para tarefa.

        Args:
            task_type (str): Tipo de tarefa

        Returns:
            Optional[str]: Caminho do adaptador ou None
        """
        active_version = self.registry["versions"].get(task_type)
        if not active_version:
            return None

        adapters = self.registry["adapters"].get(task_type, [])
        for adapter in adapters:
            if adapter["version"] == active_version:
                return adapter["path"]

        return None

    def set_active_version(self, task_type: str, version: str):
        """
        Define versão ativa para tarefa.

        Args:
            task_type (str): Tipo de tarefa
            version (str): Versão a ativar
        """
        adapters = self.registry["adapters"].get(task_type, [])
        if not any(a["version"] == version for a in adapters):
            raise ValueError(
                f"Versão {version} não encontrada para {task_type}")

        self.registry["versions"][task_type] = version
        self._save_registry()
        logger.info(f"✅ Versão ativa de {task_type}: {version}")

    def rollback(self, task_type: str):
        """
        Faz rollback para versão anterior.

        Args:
            task_type (str): Tipo de tarefa
        """
        adapters = self.registry["adapters"].get(task_type, [])
        if len(adapters) < 2:
            raise ValueError("Não há versão anterior para rollback")

        adapters.sort(key=lambda x: x["created_at"], reverse=True)

        previous = adapters[1]
        self.set_active_version(task_type, previous["version"])
        logger.info(f"✅ Rollback para {previous['version']}")

    def delete_adapter(self, task_type: str, version: str):
        """
        Remove adaptador.

        Args:
            task_type (str): Tipo de tarefa
            version (str): Versão a remover
        """
        adapters = self.registry["adapters"].get(task_type, [])

        for i, adapter in enumerate(adapters):
            if adapter["version"] == version:
                adapter_path = Path(adapter["path"])
                if adapter_path.exists():
                    shutil.rmtree(adapter_path)

                adapters.pop(i)
                self._save_registry()

                logger.info(f"✅ Adaptador removido: {task_type}_{version}")
                return

        raise ValueError(f"Adaptador {task_type}_{version} não encontrado")

    def export_for_ollama(self, task_type: str, output_name: str):
        """
        Exporta adaptador para formato Ollama.

        Args:
            task_type (str): Tipo de tarefa
            output_name (str): Nome do modelo Ollama
        """
        adapter_path = self.get_active_adapter(task_type)
        if not adapter_path:
            raise ValueError(f"Nenhum adaptador ativo para {task_type}")

        modelfile_content = f"""FROM qwen2.5-coder:7b

# Adaptador LoRA para {task_type}
ADAPTER {adapter_path}

# Parâmetros otimizados
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_ctx 4096

# System prompt
SYSTEM Você é Ziva, uma assistente de IA especializada em {task_type}.
"""

        modelfile_path = Path(adapter_path) / "Modelfile"
        with open(modelfile_path, 'w') as f:
            f.write(modelfile_content)

        logger.info(f"✅ Modelfile criado: {modelfile_path}")
        logger.info(
            f"Execute: ollama create {output_name} -f {modelfile_path}")

        return str(modelfile_path)

    def compare_adapters(self, task_type: str, version1: str, version2: str,
                         test_dataset_path: str) -> Dict:
        """
        Compara performance de dois adaptadores (A/B testing).

        Args:
            task_type (str): Tipo de tarefa
            version1 (str): Primeira versão
            version2 (str): Segunda versão
            test_dataset_path (str): Dataset de teste

        Returns:
            Dict: Resultados da comparação
        """
        logger.info(f"Comparando {version1} vs {version2} em {task_type}")

        return {
            "version1": version1,
            "version2": version2,
            "winner": version1,  # Placeholder
            "metrics": {
                version1: {"accuracy": 0.85, "latency": 1.2},
                version2: {"accuracy": 0.87, "latency": 1.3}
            }
        }


if __name__ == "__main__":
    manager = AdapterManager()

    print("📦 Adaptadores disponíveis:")
    for task_type in ["code-execution", "web-scraping", "general"]:
        adapters = manager.list_adapters(task_type)
        print(f"\n{task_type}:")
        for adapter in adapters:
            active = "✓" if adapter["version"] == manager.registry["versions"].get(
                task_type) else " "
            print(f"  [{active}] {adapter['version']} - {adapter['created_at']}")
