from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, Range
import uuid
import time
import os
from typing import List, Dict, Any, Optional
from core.vector_store_base import VectorStoreBase
from core.sync_manager import SyncManager

class QdrantVectorStore(VectorStoreBase):
    """
    Implementação do VectorStore usando Qdrant.
    """

    def __init__(self, collection_name="main_knowledge", qdrant_url=None):
        if qdrant_url is None:
            qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        
        self.client = QdrantClient(url=qdrant_url)
        self.collection_name = collection_name
        self.sync_manager = SyncManager(qdrant_url=qdrant_url)
        self._init_collection()

    def _init_collection(self):
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=2560, distance=Distance.COSINE),
            )

    def add_text(self, text: str, embedding: List[float], metadata: Optional[Dict] = None) -> Optional[str]:
        if self.exists_similar(embedding, threshold=0.95):
            if os.getenv("ZIVA_VERBOSE", "false").lower() == "true":
                print("Duplicate detected. Skipping.")
            return None

        point_id = self.sync_manager.add_to_staging(
            text=text,
            embedding=embedding,
            metadata=metadata
        )

        transferred = self.sync_manager.transfer_staging_to_main()
        if transferred > 0 and os.getenv("ZIVA_VERBOSE", "false").lower() == "true":
            print(f"✅ Transferred {transferred} docs to main")

        return point_id

    def add_texts(self, texts: List[str], embeddings: List[List[float]], metadatas: Optional[List[Dict]] = None) -> List[str]:
        points = []
        ids = []

        for i, (text, emb) in enumerate(zip(texts, embeddings)):
            point_id = str(uuid.uuid4())
            payload = {"text": text, "timestamp": time.time()}
            if metadatas and i < len(metadatas):
                payload.update(metadatas[i])

            points.append(
                PointStruct(id=point_id, vector=emb, payload=payload)
            )
            ids.append(point_id)

        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
        return ids

    def exists_similar(self, embedding: List[float], threshold: float = 0.95) -> bool:
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=embedding,
            limit=1
        ).points

        if results and results[0].score >= threshold:
            return True
        return False

    def search(self, embedding: List[float], limit: int = 5, filters: Optional[Dict] = None, query_text: Optional[str] = None) -> List[Dict]:
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=embedding,
            limit=limit,
            query_filter=filters
        ).points

        return [{"text": r.payload["text"], "score": r.score, "metadata": r.payload} for r in results]

    def scroll(self, limit: int = 100, offset: Any = None) -> tuple[List[Dict], Any]:
        result = self.client.scroll(
            collection_name=self.collection_name,
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=True
        )
        points, next_offset = result
        docs = []
        for p in points:
            docs.append({
                "id": p.id,
                "text": p.payload.get("text", ""),
                "vector": p.vector,
                "metadata": p.payload
            })
        return docs, next_offset

    def delete_old_points(self, days: int) -> int:
        cutoff = time.time() - (days * 86400)
        try:
            # Qdrant delete returns UpdateResult, we might not get exact count easily
            # but we can try to filter and delete
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="timestamp",
                            range=Range(lt=cutoff)
                        )
                    ]
                )
            )
            return 0 # Simplified: Qdrant doesn't return deleted count directly here
        except Exception as e:
            print(f"Error deleting old points: {e}")
            return -1

    def get_stats(self) -> Dict[str, Any]:
        try:
            count_result = self.client.count(collection_name=self.collection_name)
            info = self.client.get_collection(collection_name=self.collection_name)
            return {
                "total_points": count_result.count,
                "status": info.status,
                "vectors_count": info.points_count,
                "segments": info.segments_count
            }
        except Exception as e:
            return {"error": str(e)}
