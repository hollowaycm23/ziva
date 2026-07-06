"""
Sync Manager - Gerencia sincronização entre Ziva e Gabrielle usando staging DB
"""
import os
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import time
import uuid
from typing import List, Dict, Any


class SyncManager:
    """
    Gerencia sincronização entre collections usando staging database.
    """

    def __init__(self, qdrant_url: str = "http://localhost:6333"):
        self.client = QdrantClient(url=qdrant_url)
        self.main_collection = "main_knowledge"
        self.staging_collection = "staging_sync"
        self.log_collection = "sync_log"
        self._connect_with_retry()

    def _connect_with_retry(self, max_retries: int = 5, delay: int = 2):
        import httpx
        from qdrant_client.http.exceptions import ResponseHandlingException
        last_error = None
        for attempt in range(max_retries):
            try:
                self._ensure_collections()
                return
            except (httpx.ConnectError, ResponseHandlingException,
                    ConnectionRefusedError) as e:
                last_error = e
                print(
                    f"⚠️ Qdrant connection failed (attempt {attempt + 1}/"
                    f"{max_retries}): {e}")
                time.sleep(delay)
        print(f"❌ Could not connect to Qdrant after {max_retries} attempts.")
        raise last_error

    def _ensure_collections(self):
        collections = {
            c.name for c in self.client.get_collections().collections}
        vec_size = int(os.getenv("QDRANT_VECTOR_SIZE", "768"))
        if self.main_collection not in collections:
            if "knowledge" in collections:
                print(f"📦 Migrando 'knowledge' → '{self.main_collection}'...")
                self._migrate_collection("knowledge", self.main_collection)
            else:
                self.client.create_collection(
                    collection_name=self.main_collection,
                    vectors_config=VectorParams(
                        size=vec_size, distance=Distance.COSINE, on_disk=False))
                print(f"✅ Created collection: {self.main_collection}")
        if self.staging_collection not in collections:
            self.client.create_collection(
                collection_name=self.staging_collection,
                vectors_config=VectorParams(
                    size=vec_size, distance=Distance.COSINE, on_disk=False))
            print(f"✅ Created collection: {self.staging_collection}")
        if self.log_collection not in collections:
            self.client.create_collection(
                collection_name=self.log_collection,
                vectors_config=VectorParams(
                    size=128, distance=Distance.COSINE, on_disk=True))
            print(f"✅ Created collection: {self.log_collection}")

    def _migrate_collection(self, old_name: str, new_name: str):
        old_info = self.client.get_collection(old_name)
        self.client.create_collection(
            collection_name=new_name,
            vectors_config=old_info.config.params.vectors)
        offset = None
        while True:
            result = self.client.scroll(
                collection_name=old_name,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=True)
            points, offset = result
            if not points:
                break
            self.client.upsert(
                collection_name=new_name,
                points=[{"id": p.id, "vector": p.vector, "payload": p.payload}
                        for p in points])
        print(f"✅ Migrated {old_name} → {new_name}")

    def add_to_staging(self, text: str, embedding: List[float], metadata: Dict = None) -> str:
        """
        Adiciona novo documento ao staging.
        """
        point_id = str(uuid.uuid4())
        payload = {
            "text": text, "timestamp": time.time(), "synced": False,
            "sync_target": "gabrielle", **(metadata or {})}
        self.client.upsert(
            collection_name=self.staging_collection,
            points=[PointStruct(id=point_id, vector=embedding,
                                payload=payload)])
        return point_id

    def transfer_staging_to_main(self) -> int:
        """
        Transfere documentos do staging para main.
        """
        result = self.client.scroll(
            collection_name=self.staging_collection,
            limit=100, with_payload=True, with_vectors=True)
        points = result[0]
        if not points:
            return 0
        self.client.upsert(
            collection_name=self.main_collection,
            points=[PointStruct(id=p.id, vector=p.vector, payload=p.payload)
                    for p in points])

        # Remove from staging after successful transfer
        self.client.delete(
            collection_name=self.staging_collection,
            points_selector=[p.id for p in points]
        )

        self._log_sync_operation(
            operation="staging_to_main", count=len(points),
            point_ids=[str(p.id) for p in points])
        return len(points)

    def get_pending_sync(self, limit: int = 100) -> List[Dict]:
        """
        Retorna documentos pendentes de sincronização.
        """
        result = self.client.scroll(
            collection_name=self.staging_collection,
            limit=limit, with_payload=True, with_vectors=True)
        points = result[0]
        return [{"id": str(p.id), "vector": p.vector, "payload": p.payload}
                for p in points]

    def mark_as_synced(self, point_ids: List[str]):
        """
        Marca documentos como sincronizados.
        """
        for point_id in point_ids:
            self.client.set_payload(
                collection_name=self.staging_collection,
                payload={"synced": True, "sync_timestamp": time.time()},
                points=[point_id])
        self._log_sync_operation(
            operation="marked_synced", count=len(point_ids),
            point_ids=point_ids)

    def clear_synced_staging(self) -> int:
        """
        Remove documentos já sincronizados do staging.
        """
        result = self.client.scroll(
            collection_name=self.staging_collection,
            limit=1000, with_payload=True)
        synced_ids = [str(p.id)
                      for p in result[0] if p.payload.get("synced", False)]
        if synced_ids:
            self.client.delete(
                collection_name=self.staging_collection,
                points_selector=synced_ids)
        return len(synced_ids)

    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas de sincronização.
        """
        main_count = self.client.count(self.main_collection).count
        staging_count = self.client.count(self.staging_collection).count
        result = self.client.scroll(
            collection_name=self.staging_collection,
            limit=1000, with_payload=True)
        pending = sum(
            1 for p in result[0] if not p.payload.get("synced", False))
        synced = staging_count - pending
        return {
            "main_documents": main_count, "staging_total": staging_count,
            "staging_pending": pending, "staging_synced": synced}

    def _log_sync_operation(self, operation: str,
                            count: int, point_ids: List[str]):
        log_id = str(uuid.uuid4())
        dummy_vector = [0.0] * 128
        self.client.upsert(
            collection_name=self.log_collection,
            points=[PointStruct(
                id=log_id, vector=dummy_vector,
                payload={
                    "operation": operation, "count": count,
                    "point_ids": point_ids[:10], "timestamp": time.time()})])
