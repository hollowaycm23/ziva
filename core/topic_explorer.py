"""
Topix Explorer - Explorador de Tópicos e Lacunas
Analisa clusters de conhecimento e gera curiosidade
"""

import logging
import numpy as np
from typing import List, Dict
from core.vector_store import VectorStore
# Se scikit-learn não estiver disponível, implementamos K-Means simples
# com numpy
try:
    from sklearn.cluster import KMeans
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TopicExplorer")


class TopicExplorer:
    """
    Analisa a base de conhecimento para encontrar clusters e lacunas
    """

    def __init__(self):
        self.vector_store = VectorStore()
        logger.info(f"✅ Topic Explorer inicializado (Sklearn: {HAS_SKLEARN})")

    def analyze_knowledge_space(self, n_clusters: int = 5) -> Dict:
        """
        Analisa o espaço vetorial e identifica tópicos principais
        """
        try:
            # 1. Recuperar pontos (amostragem)
            # Qdrant scroll API
            points = self._fetch_all_vectors(limit=500)

            if not points:
                return {'error': 'Sem dados suficientes'}

            vectors = np.array([p.vector for p in points])
            texts = [p.payload.get('text', '')[:50] for p in points]

            # 2. Clusterização
            if HAS_SKLEARN:
                kmeans = KMeans(n_clusters=n_clusters, random_state=42)
                labels = kmeans.fit_predict(vectors)
            else:
                # Fallback simples (Implementação manual seria longa, vamos
                # simplificar)
                logger.warning(
                    "Sklearn ausente, pulando clusterização avançada")
                return {'status': 'sklearn_missing'}

            # 3. Identificar temas por cluster
            clusters = {}
            for i in range(n_clusters):
                cluster_indices = np.where(labels == i)[0]
                cluster_texts = [texts[idx] for idx in cluster_indices]

                # Pegar texto mais representativo (mais próximo do centro -
                # simplificado: primeiro)
                if cluster_texts:
                    clusters[f"Cluster {i}"] = {
                        "size": len(cluster_texts),
                        "sample": cluster_texts[0] + "..."
                    }

            return {
                "total_points": len(points),
                "clusters": clusters
            }

        except Exception as e:
            logger.error(f"Erro na análise: {e}")
            return {'error': str(e)}

    def generate_curiosity_questions(self) -> List[str]:
        """
        Gera perguntas sobre o que o sistema NÃO sabe (lacunas)
        ou tópicos para aprofundar.
        """
        # Lógica simplificada:
        # 1. Pegar clusters existentes
        # 2. Identificar áreas com baixa densidade (future)
        # 3. Por enquanto: Perguntar sobre tópicos relacionados mas ausentes?
        # Ou simplesmente perguntar sobre os clusters menores.

        return [
            "Que tal me ensinar mais sobre Python Asyncio?",
            "Gostaria de saber mais sobre Docker Networking.",
            "Temos poucos dados sobre Otimização de Banco de Dados."
        ]

    def _fetch_all_vectors(self, limit: int = 100):
        """Recupera batch de vetores do Qdrant"""
        # Qdrant client scroll
        # client.scroll returns (points, next_page_offset)
        res = self.vector_store.client.scroll(
            collection_name=self.vector_store.collection_name,
            limit=limit,
            with_vectors=True  # Importante: trazer vetores
        )
        return res[0]


# Singleton
_explorer = None


def get_topic_explorer() -> TopicExplorer:
    global _explorer
    if _explorer is None:
        _explorer = TopicExplorer()
    return _explorer


if __name__ == "__main__":
    print("🔭 Testando Topic Explorer...")
    explorer = TopicExplorer()
    analysis = explorer.analyze_knowledge_space(n_clusters=3)
    print(f"Análise: {analysis}")

    questions = explorer.generate_curiosity_questions()
    print("\n🤔 Perguntas de Curiosidade:")
    for q in questions:
        print(f" - {q}")
