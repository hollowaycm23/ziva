"""
Model Cache - Singleton para compartilhamento de modelos ML
"""

from sentence_transformers import SentenceTransformer, CrossEncoder
from threading import Lock
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ModelCache:
    """
    Thread-safe singleton cache para modelos de embedding e reranking.
    """

    _instance: Optional['ModelCache'] = None
    _lock: Lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._encoders: Dict[str,
                                                  SentenceTransformer] = {}
                    cls._instance._cross_encoders: Dict[str, CrossEncoder] = {}
        return cls._instance

    def get_encoder(
            self,
            model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'
    ) -> SentenceTransformer:
        """
        Retorna encoder com lazy loading e cache.
        """
        if model_name not in self._encoders:
            with self._lock:
                if model_name not in self._encoders:
                    logger.info(f"🔄 Loading SentenceTransformer: {model_name}")
                    self._encoders[model_name] = SentenceTransformer(
                        model_name)
                    logger.info(f"✅ Encoder ready: {model_name}")
        return self._encoders[model_name]

    def get_cross_encoder(
            self, model_name: str = 'BAAI/bge-reranker-base') -> CrossEncoder:
        """
        Retorna cross-encoder com lazy loading e cache.
        """
        if model_name not in self._cross_encoders:
            with self._lock:
                if model_name not in self._cross_encoders:
                    logger.info(f"🔄 Loading CrossEncoder: {model_name}")
                    import torch
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                    self._cross_encoders[model_name] = CrossEncoder(
                        model_name,
                        device=device
                    )
                    logger.info(
                        f"✅ CrossEncoder ready: {model_name} on {device}")
        return self._cross_encoders[model_name]

    def clear_cache(self):
        """Limpa cache"""
        with self._lock:
            self._encoders.clear()
            self._cross_encoders.clear()
            logger.info("🧹 Model cache cleared")


_model_cache = ModelCache()


def get_encoder(
    model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'
) -> SentenceTransformer:
    """
    Helper global para obter encoder.
    """
    return _model_cache.get_encoder(model_name)


def get_cross_encoder(
        model_name: str = 'BAAI/bge-reranker-base') -> CrossEncoder:
    """
    Helper global para obter cross-encoder.
    """
    return _model_cache.get_cross_encoder(model_name)