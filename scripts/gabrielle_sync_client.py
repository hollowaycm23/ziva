"""
Script para Gabrielle - Cliente de Sincronização

Este script deve ser executado em Gabrielle para sincronizar com Ziva.
"""
import requests
import time
from typing import List, Dict


class ZivaSyncClient:
    """
    Cliente para sincronizar conhecimento de Ziva.
    """

    def __init__(self, ziva_url: str = "http://localhost:8000"):
        self.ziva_url = ziva_url
        self.sync_endpoint = f"{ziva_url}/sync"

    def fetch_pending_documents(self, limit: int = 100) -> List[Dict]:
        """
        Busca documentos pendentes de sincronização.

        Returns:
            Lista de documentos para sincronizar
        """
        try:
            response = requests.get(
                f"{self.sync_endpoint}/pending",
                params={"limit": limit},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            print(f"📥 Fetched {data['count']} pending documents from Ziva")
            return data['documents']

        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching documents: {e}")
            return []

    def mark_as_synced(self, point_ids: List[str]) -> bool:
        """
        Marca documentos como sincronizados.

        Args:
            point_ids: IDs dos documentos sincronizados

        Returns:
            True se bem-sucedido
        """
        try:
            response = requests.post(
                f"{self.sync_endpoint}/mark_synced",
                json={"point_ids": point_ids},
                timeout=10
            )
            response.raise_for_status()

            print(f"✅ Marked {len(point_ids)} documents as synced")
            return True

        except requests.exceptions.RequestException as e:
            print(f"❌ Error marking synced: {e}")
            return False

    def sync_to_local_qdrant(
            self,
            documents: List[Dict],
            local_qdrant_url: str = "http://localhost:6333"):
        """
        Sincroniza documentos para Qdrant local de Gabrielle.

        Args:
            documents: Documentos a sincronizar
            local_qdrant_url: URL do Qdrant local
        """
        from qdrant_client import QdrantClient
        from qdrant_client.models import PointStruct

        client = QdrantClient(url=local_qdrant_url)
        collection_name = "gabrielle_knowledge"

        # Criar collection se não existir
        try:
            client.get_collection(collection_name)
        except BaseException:
            from qdrant_client.models import VectorParams, Distance
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=768,
                    distance=Distance.COSINE
                )
            )
            print(f"✅ Created collection: {collection_name}")

        # Inserir documentos
        points = [
            PointStruct(
                id=doc['id'],
                vector=doc['vector'],
                payload=doc['payload']
            )
            for doc in documents
        ]

        client.upsert(
            collection_name=collection_name,
            points=points
        )

        print(f"💾 Synced {len(documents)} documents to local Qdrant")

    def run_sync_cycle(self):
        """
        Executa um ciclo completo de sincronização.
        """
        print("\n" + "=" * 80)
        print("🔄 GABRIELLE SYNC CYCLE")
        print("=" * 80)

        # 1. Buscar documentos pendentes
        documents = self.fetch_pending_documents()

        if not documents:
            print("📭 No pending documents")
            return

        # 2. Sincronizar para Qdrant local
        try:
            self.sync_to_local_qdrant(documents)
        except Exception as e:
            print(f"❌ Error syncing to local Qdrant: {e}")
            return

        # 3. Marcar como sincronizado em Ziva
        point_ids = [doc['id'] for doc in documents]
        success = self.mark_as_synced(point_ids)

        if success:
            print(f"✅ Sync cycle completed: {len(documents)} documents")
        else:
            print("⚠️ Sync cycle completed but failed to mark as synced")

    def run_continuous_sync(self, interval_seconds: int = 300):
        """
        Executa sincronização contínua.

        Args:
            interval_seconds: Intervalo entre ciclos (padrão: 5 minutos)
        """
        print(f"🔄 Starting continuous sync (interval: {interval_seconds}s)")
        print("Press Ctrl+C to stop")

        try:
            while True:
                self.run_sync_cycle()
                print(f"\n⏳ Waiting {interval_seconds}s for next cycle...")
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n\n🛑 Sync stopped by user")


if __name__ == "__main__":
    # Exemplo de uso
    # Zivas Tailscale IP: 100.105.168.115
    client = ZivaSyncClient(ziva_url="http://100.105.168.115:8000")

    # Opção 1: Sync único
    client.run_sync_cycle()

    # Opção 2: Sync contínuo (a cada 5 minutos)
    client.run_continuous_sync(interval_seconds=300)
