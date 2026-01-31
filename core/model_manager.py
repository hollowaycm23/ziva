"""
Model Manager - Gerenciador de Modelos LLM
Responsável por baixar, listar e gerenciar modelos no Ollama
"""

import logging
import requests
from typing import List, Dict
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ModelManager")


@dataclass
class ModelInfo:
    name: str
    size: str
    digest: str
    details: Dict


class ModelManager:
    """
    Gerencia múltiplos modelos no Ollama
    """

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.base_url = ollama_url
        self.session = requests.Session()
        logger.info(f"✅ Model Manager conectado em {self.base_url}")

    def list_models(self) -> List[ModelInfo]:
        """Lista modelos disponíveis localmente"""
        try:
            resp = self.session.get(f"{self.base_url}/api/tags")
            resp.raise_for_status()
            data = resp.json()

            models = []
            for m in data.get('models', []):
                models.append(ModelInfo(
                    name=m['name'],
                    size=f"{m.get('size', 0) / 1e9:.2f} GB",
                    digest=m.get('digest', '')[:12],
                    details=m.get('details', {})
                ))
            return models
        except Exception as e:
            logger.error(f"Erro ao listar modelos: {e}")
            return []

    def load_model(self, model_name: str) -> bool:
        """
        Carrega um modelo na memória (preload)
        """
        try:
            logger.info(f"⏳ Carregando modelo {model_name}...")
            self.known_models = {
                "coding": ["qwen2.5-coder:7b", "codellama:7b"],
                "reasoning": ["deepseek-r1:8b"],
                "general": ["llama3:8b", "mistral:7b", "ziva-base:latest"],
                "vision": ["llava:7b", "moondream:latest"]
            }
            payload = {
                "model": model_name,
                "keep_alive": "5m"
            }
            resp = self.session.post(
                f"{self.base_url}/api/generate", json=payload)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {e}")
            return False

    def pull_model(self, model_name: str) -> bool:
        """
        Baixa um novo modelo do Ollama Library
        """
        try:
            logger.info(f"⬇️ Iniciando download de {model_name}...")
            resp = self.session.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name, "stream": False},
                timeout=600
            )

            if resp.status_code == 200:
                logger.info(f"✅ Modelo {model_name} baixado com sucesso")
                return True
            else:
                logger.error(f"Falha no download: {resp.text}")
                return False

        except Exception as e:
            logger.error(f"Erro no pull do modelo: {e}")
            return False

    def get_loaded_models(self) -> List[str]:
        """Retorna modelos atualmente carregados na RAM/VRAM"""
        try:
            resp = self.session.get(f"{self.base_url}/api/ps")
            if resp.status_code == 200:
                data = resp.json()
                return [m['name'] for m in data.get('models', [])]
            return []
        except Exception as e:
            logger.warning(f"Erro ao checar modelos carregados: {e}")
            return []


_manager = None


def get_model_manager() -> ModelManager:
    global _manager
    if _manager is None:
        _manager = ModelManager()
    return _manager


if __name__ == "__main__":
    print("🤖 Testando Model Manager...")
    mgr = ModelManager()

    print("\n📦 Modelos Locais:")
    models = mgr.list_models()
    for m in models:
        print(f" - {m.name} ({m.size})")

    print(f"\n🧠 Modelos Carregados: {mgr.get_loaded_models()}")