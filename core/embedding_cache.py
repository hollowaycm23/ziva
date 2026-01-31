"""
Embedding Cache
Cache de embeddings para reduzir latência
"""

import json
import hashlib
import pickle
import logging
from pathlib import Path
from typing import Optional
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EmbeddingCache")


class EmbeddingCache:
    """Cache persistente de embeddings"""

    def __init__(self, cache_dir: str = "./embedding_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.index_file = self.cache_dir / "index.json"
        self.index = self._load_index()
        self.hits = 0
        self.misses = 0

    def _load_index(self) -> dict:
        """Carrega índice de cache"""
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_index(self):
        """Salva índice de cache"""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)

    def _get_hash(self, text: str) -> str:
        """Gera hash do texto"""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def get(self, text: str) -> Optional[np.ndarray]:
        """Busca embedding no cache"""
        text_hash = self._get_hash(text)
        if text_hash in self.index:
            cache_file = self.cache_dir / f"{text_hash}.pkl"
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    embedding = pickle.load(f)
                self.hits += 1
                logger.debug(f"✓ Cache hit: {text[:50]}...")
                return embedding
        self.misses += 1
        logger.debug(f"✗ Cache miss: {text[:50]}...")
        return None

    def set(self, text: str, embedding: np.ndarray):
        """Armazena embedding no cache"""
        text_hash = self._get_hash(text)
        cache_file = self.cache_dir / f"{text_hash}.pkl"
        with open(cache_file, 'wb') as f:
            pickle.dump(embedding, f)
        self.index[text_hash] = {
            'text_preview': text[:100],
            'shape': list(embedding.shape),
            'cached_at': str(Path(cache_file).stat().st_mtime)
        }
        self._save_index()
        logger.debug(f"✓ Cached: {text[:50]}...")

    def clear(self):
        """Limpa todo o cache"""
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()
        self.index = {}
        self._save_index()
        logger.info("🗑️ Cache cleared")

    def get_stats(self) -> dict:
        """Retorna estatísticas do cache"""
        total_requests = self.hits + self.misses
        hit_rate = (
            self.hits / total_requests * 100) if total_requests > 0 else 0
        cache_size = sum(
            f.stat().st_size for f in self.cache_dir.glob("*.pkl"))
        return {
            'total_entries': len(self.index),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'cache_size_mb': cache_size / (1024 * 1024)
        }


if __name__ == "__main__":
    cache = EmbeddingCache()
    test_text = "Como listar arquivos no Linux?"
    fake_embedding = np.random.rand(768)
    result = cache.get(test_text)
    print(f"Primeira busca: {result is None} (esperado: True)")
    cache.set(test_text, fake_embedding)
    result = cache.get(test_text)
    print(f"Segunda busca: {result is not None} (esperado: True)")
    if result is not None:
        print(f"Embedding shape: {result.shape}")
    stats = cache.get_stats()
    print("\n📊 Estatísticas:")
    for key, value in stats.items():
        print(f"  {key}: {value}")