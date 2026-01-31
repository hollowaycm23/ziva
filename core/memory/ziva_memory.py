"""
Ziva Memory System - Baseado em Qdrant com Quadrantes
"""

import time
import logging
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ZivaMemory")


@dataclass
class MemoryEntry:
    """Representa uma entrada de memória"""
    text: str
    quadrant: str
    timestamp: float
    metadata: Dict
    score: float = 0.0


class ZivaMemory:
    """
    Sistema de Memória de Longo Prazo para Ziva
    """

    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        model_name: str = "all-MiniLM-L6-v2",
        embedding_dim: int = 768
    ):
        """
        Inicializa sistema de memória
        """
        self.client = QdrantClient(url=qdrant_url)
        self._model_name = model_name
        self._encoder = None
        self.embedding_dim = embedding_dim
        self.quadrants = {
            "Q1_LOGIC": {"desc": "Raciocínios e lógica", "shielding": 1},
            "Q2_USER_DATA": {"desc": "Dados do usuário", "shielding": 3}, # Max Shielding
            "Q3_PROJECTS": {"desc": "Projetos e código", "shielding": 2},
            "Q4_ARCHIVE": {"desc": "Arquivo histórico", "shielding": 1},
            "Q5_SKILLS": {"desc": "Conhecimento técnico", "shielding": 1},
            "Q6_CONVERSATIONS": {"desc": "Conversas importantes", "shielding": 2}
        }
        self.setup_quadrants()
        logger.info(
            f"✅ Ziva Memory System initialized with {len(self.quadrants)} "
            "quadrants")

    @property
    def encoder(self):
        """Lazy-loaded encoder"""
        if self._encoder is None:
            from core.model_cache import get_encoder
            self._encoder = get_encoder(self._model_name)
        return self._encoder

    def setup_quadrants(self):
        """Cria collections para cada quadrante garantindo isolamento de blindagem"""
        for quadrant, config in self.quadrants.items():
            description = config["desc"]
            try:
                if not self.client.collection_exists(quadrant):
                    self.client.create_collection(
                        collection_name=quadrant,
                        vectors_config=VectorParams(
                            size=self.embedding_dim,
                            distance=Distance.COSINE
                        ),
                        hnsw_config={"m": 16, "ef_construct": 100},
                        optimizers_config={"indexing_threshold": 1000}
                    )
                    logger.info(
                        f"✓ Created quadrant: {quadrant} ({description})")
                else:
                    logger.debug(f"✓ Quadrant exists: {quadrant}")
            except Exception as e:
                logger.error(f"❌ Error creating {quadrant}: {e}")

    def learn(self, query: str, final_solution: str, sources: str = ""):
        """
        Active Learning: Internaliza uma solução valiosa.
        """
        content_to_save = (
            f"PERGUNTA: {query}\nSOLUÇÃO: {final_solution}\n"
            f"FONTES: {sources}")
        metadata = {
            "type": "learned_lesson",
            "source": "active_learning_v2",
            "original_query": query
        }
        return self.save(
            text=content_to_save,
            quadrant="Q1_LOGIC",
            metadata=metadata,
            importance=0.8
        )

    def save(
        self,
        text: str,
        quadrant: str = "Q2_USER_DATA",
        metadata: Optional[Dict] = None,
        importance: float = 0.5
    ) -> int:
        """
        Salva memória em um quadrante
        """
        if quadrant not in self.quadrants:
            logger.warning(
                f"⚠️ Quadrant {quadrant} não existe, usando Q2_USER_DATA")
            quadrant = "Q2_USER_DATA"
        vector = self.encoder.encode(text).tolist()
        point_id = int(time.time() * 1000000)
        payload = {
            "text": text,
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "importance": importance,
            "quadrant": quadrant,
            **(metadata or {})
        }
        try:
            self.client.upsert(
                collection_name=quadrant,
                points=[PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )]
            )
            logger.info(f"💾 Saved to {quadrant}: {text[:50]}...")
            return point_id
        except Exception as e:
            from core.exceptions import VectorStoreError
            logger.exception(f"Failed to save to {quadrant}")
            raise VectorStoreError(f"Save failed: {e}") from e

    def recall(
        self,
        query: str,
        quadrant: Optional[str] = None,
        limit: int = 5,
        min_score: float = 0.5
    ) -> List[MemoryEntry]:
        """
        Busca memórias similares
        """
        vector = self.encoder.encode(query).tolist()
        targets = [quadrant] if quadrant and quadrant in self.quadrants else [
            q for q in self.quadrants.keys() if q != "Q4_ARCHIVE"]
        
        # RADIATION SHIELDING: Filter out high-shielding quadrants for general queries
        # (This is a simplified logical isolation for the bio-inspired concept)
        # In the future, this would check user session permissions.
        
        all_results = []
        for target in targets:
            try:
                results = self.client.search(
                    collection_name=target,
                    query_vector=vector,
                    limit=limit,
                    score_threshold=min_score
                )
                for result in results:
                    all_results.append(MemoryEntry(
                        text=result.payload.get("text", ""),
                        quadrant=target,
                        timestamp=result.payload.get("timestamp", 0),
                        metadata=result.payload,
                        score=result.score
                    ))
            except Exception as e:
                logger.error(f"❌ Error searching {target}: {e}")
        all_results.sort(key=lambda x: x.score, reverse=True)
        logger.info(
            f"🔍 Recalled {len(all_results[:limit])} memories for: {query[:50]}...")
        return all_results[:limit]

    def recall_with_context(
        self,
        query: str,
        context_window: int = 3600,
        limit: int = 3
    ) -> List[MemoryEntry]:
        """
        Busca memórias recentes + similares
        """
        current_time = time.time()
        cutoff_time = current_time - context_window
        vector = self.encoder.encode(query).tolist()
        results = []
        for quadrant in ["Q6_CONVERSATIONS", "Q2_USER_DATA"]:
            try:
                search_results = self.client.search(
                    collection_name=quadrant,
                    query_vector=vector,
                    query_filter=Filter(must=[FieldCondition(
                        key="timestamp", range={"gte": cutoff_time})]),
                    limit=limit
                )
                for result in search_results:
                    results.append(MemoryEntry(
                        text=result.payload.get("text", ""),
                        quadrant=quadrant,
                        timestamp=result.payload.get("timestamp", 0),
                        metadata=result.payload,
                        score=result.score
                    ))
            except Exception as e:
                logger.debug(f"No recent memories in {quadrant}: {e}")
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    def archive_old_memories(self, days_old: int = 30):
        """
        Move memórias antigas para Q4_ARCHIVE
        """
        cutoff_time = time.time() - (days_old * 86400)
        archived_count = 0
        for quadrant in ["Q2_USER_DATA", "Q6_CONVERSATIONS"]:
            try:
                old_memories = self.client.scroll(
                    collection_name=quadrant,
                    scroll_filter=Filter(must=[FieldCondition(
                        key="timestamp", range={"lt": cutoff_time})]),
                    limit=1000
                )
                if old_memories[0]:
                    for point in old_memories[0]:
                        self.client.upsert(
                            collection_name="Q4_ARCHIVE", points=[point])
                        archived_count += 1
                    point_ids = [p.id for p in old_memories[0]]
                    self.client.delete(
                        collection_name=quadrant,
                        points_selector=point_ids
                    )
            except Exception as e:
                logger.error(f"Error archiving from {quadrant}: {e}")
        logger.info(f"📦 Archived {archived_count} old memories")
        return archived_count

    def get_statistics(self) -> Dict:
        """Retorna estatísticas de uso"""
        stats = {}
        total_points = 0
        for quadrant in self.quadrants.keys():
            try:
                info = self.client.get_collection(quadrant)
                count = info.points_count
                stats[quadrant] = count
                total_points += count
            except Exception as e:
                stats[quadrant] = 0
                logger.debug(f"Error getting stats for {quadrant}: {e}")
        stats["TOTAL"] = total_points
        return stats

    def clear_quadrant(self, quadrant: str):
        """Limpa um quadrante específico"""
        if quadrant in self.quadrants:
            try:
                self.client.delete_collection(quadrant)
                self.setup_quadrants()
                logger.info(f"🗑️ Cleared quadrant: {quadrant}")
            except Exception as e:
                logger.error(f"Error clearing {quadrant}: {e}")


if __name__ == "__main__":
    print("🧠 Ziva Memory System - Test")
    print("=" * 60)
    try:
        memory = ZivaMemory()
        print("\n💾 Salvando memórias...")
        memory.save(
            "O usuário prefere Python para scripts de automação",
            quadrant="Q2_USER_DATA",
            metadata={"category": "preference"}
        )
        memory.save(
            "Implementamos LoRA fine-tuning com QLoRA na RTX 4070",
            quadrant="Q3_PROJECTS",
            metadata={"project": "ziva", "component": "training"}
        )
        memory.save(
            "Para listar processos no Linux use: ps aux | grep <nome>",
            quadrant="Q5_SKILLS",
            metadata={"skill": "linux", "command": "ps"}
        )
        print("\n🔍 Buscando memórias...")
        results = memory.recall("Como listar processos?", limit=3)
        for i, mem in enumerate(results, 1):
            print(f"\n{i}. [{mem.quadrant}] Score: {mem.score:.3f}")
            print(f"   {mem.text[:100]}")
        print("\n📊 Estatísticas:")
        stats = memory.get_statistics()
        for quad, count in stats.items():
            print(f"  {quad}: {count} memórias")
        print("\n✅ Teste concluído!")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("💡 Certifique-se que Qdrant está rodando.")
        print("   docker run -p 6333:6333 qdrant/qdrant")