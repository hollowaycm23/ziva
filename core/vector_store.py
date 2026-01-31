from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, Range, MatchAny
import uuid
import time
from pathlib import Path
from core.sync_manager import SyncManager

# Assuming local Qdrant for now.
# "protecao contra contaminacao" implicitly handled by collection separation if needed, or metadata.
# "filtro de duplicatas" handled by vector similarity check before insertion.


class VectorStore:
    """
    Gerenciador de armazenamento vetorial para RAG (Retrieval-Augmented Generation).

    Utiliza Qdrant para indexação e busca semântica de documentos.
    Handles deduplication and metadata management.
    """

    def __init__(self, collection_name="main_knowledge",
                 qdrant_url=None):
        if qdrant_url is None:
            import os
            qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        """
        Inicializa o cliente Qdrant via HTTP.

        Args:
            collection_name (str): Nome da coleção no Qdrant.
            qdrant_url (str): URL do servidor Qdrant.
        """
        self.client = QdrantClient(url=qdrant_url)
        self.collection_name = collection_name
        self.sync_manager = SyncManager(qdrant_url=qdrant_url)
        self._init_collection()

    def _init_collection(self):
        """
        Inicializa a coleção no Qdrant se ela não existir.

        Define a configuração vetorial (dimensão 768 para nomic-embed-text).
        """
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=768, distance=Distance.COSINE),
            )

    def add_text(self, text, embedding, metadata=None):
        """
        Adiciona um texto vetorizado ao STAGING (não bloqueia main).

        Args:
            text (str): O conteúdo textual original.
            embedding (list): O vetor de float representando o texto.
            metadata (dict, optional): Metadados adicionais.

        Returns:
            str: ID do ponto inserido ou None se for duplicata.
        """
        # Verificar duplicidade apenas no staging (rápido)
        if self.exists_similar(embedding, threshold=0.95):
            import os
            if os.getenv("ZIVA_VERBOSE", "false").lower() == "true":
                print("Duplicate detected. Skipping.")
            return None

        # Adicionar ao staging (sem lock na main)
        point_id = self.sync_manager.add_to_staging(
            text=text,
            embedding=embedding,
            metadata=metadata
        )

        # Transferir para main imediatamente (pode ser background no futuro)
        transferred = self.sync_manager.transfer_staging_to_main()
        if transferred > 0:
            import os
            if os.getenv("ZIVA_VERBOSE", "false").lower() == "true":
                print(f"✅ Transferred {transferred} docs to main")

        return point_id

    def add_texts(self, texts, embeddings, metadatas=None):
        """
        Adiciona múltiplos textos vetorizados (batch).
        """
        points = []
        ids = []

        for i, (text, emb) in enumerate(zip(texts, embeddings)):
            # Check dedup (simple check) - for batch efficiency maybe skip or optimize
            # For now, let's just insert. Optimizing dedup for batch is
            # complex.

            point_id = str(uuid.uuid4())
            payload = {"text": text, "timestamp": time.time()}
            if metadatas and i < len(metadatas):
                payload.update(metadatas[i])

            points.append(
                PointStruct(
                    id=point_id,
                    vector=emb,
                    payload=payload))
            ids.append(point_id)

        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
        return ids

    def exists_similar(self, embedding, threshold=0.95):
        """
        Verifica se existe algum vetor muito similar na base.

        Args:
            embedding (list): Vetor de consulta.
            threshold (float): Limiar de similaridade (cosseno).

        Returns:
            bool: True se encontrar similar, False caso contrário.
        """
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=embedding,
            limit=1
        ).points

        if results and results[0].score >= threshold:
            return True
        return False

    def search(self, embedding, limit=5, use_active_recall=True, filters: dict = None):
        """
        Realiza busca por similaridade semântica com Active Recall e Filtros.

        Args:
            embedding (list): Vetor de consulta.
            limit (int): Número máximo de resultados.
            use_active_recall (bool): Ativar boost para lições aprendidas (default: True)
            filters (dict, optional): Filtros de metadados do Qdrant.

        Returns:
            list: Lista de dicionários contendo texto, score e metadados.
        """
        # Fetch more results if using Active Recall for re-ranking
        fetch_limit = limit * 2 if use_active_recall else limit

        # Execute Query with Filter if present
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=embedding,
            limit=fetch_limit,
            query_filter=filters
        ).points

        formatted = [{"text": r.payload["text"], "score": r.score,
                      "metadata": r.payload} for r in results]

        # Apply Active Recall boost
        if use_active_recall and formatted:
            try:
                from core.rag_enhancement import get_recall_enhancer
                enhancer = get_recall_enhancer()
                formatted = enhancer.enhance_results(formatted)
                formatted = formatted[:limit]  # Trim after re-ranking
            except Exception as e:
                import logging
                logging.getLogger("VectorStore").warning(
                    f"Active Recall failed: {e}")

        return formatted

    def get_stats(self):
        """
        Retorna estatísticas da coleção.
        """
        try:
            count_result = self.client.count(
                collection_name=self.collection_name)
            info = self.client.get_collection(
                collection_name=self.collection_name)
            return {
                "total_points": count_result.count,
                "status": info.status,
                "vectors_count": info.points_count,
                "segments": info.segments_count
            }
        except Exception as e:
            return {"error": str(e)}

    def update_confidence(self, point_id: str, confidence: float,
                          verification_data: dict = None):
        """
        Updates the confidence score of an existing point.

        Args:
            point_id: ID of the point to update
            confidence: Confidence score (0.0 to 1.0)
            verification_data: Optional verification metadata
        """
        try:
            # Get existing point
            point = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[point_id]
            )

            if not point:
                return {"error": "Point not found"}

            # Update payload with confidence
            payload = point[0].payload
            payload["confidence"] = confidence
            payload["verified"] = confidence > 0.5

            if verification_data:
                payload["verification"] = verification_data

            # Update point
            self.client.set_payload(
                collection_name=self.collection_name,
                payload=payload,
                points=[point_id]
            )

            return {"success": True, "confidence": confidence}

        except Exception as e:
            return {"error": str(e)}
