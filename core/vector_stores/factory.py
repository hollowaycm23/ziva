import os
from typing import Optional
from core.vector_store_base import VectorStoreBase

def get_vector_store(collection_name: str = "main_knowledge") -> VectorStoreBase:
    """
    Factory para obter a implementação correta de VectorStore baseada no .env.
    """
    backend = os.getenv("ZIVA_VECTOR_STORE_BACKEND", "qdrant").lower()

    if backend == "qdrant":
        from core.vector_stores.qdrant_store import QdrantVectorStore
        return QdrantVectorStore(collection_name=collection_name)
    
    elif backend == "faiss":
        from core.vector_stores.faiss_store import FAISSVectorStore
        return FAISSVectorStore(collection_name=collection_name)
    
    elif backend == "elasticsearch" or backend == "es":
        from core.vector_stores.elasticsearch_store import ElasticsearchVectorStore
        return ElasticsearchVectorStore(collection_name=collection_name)
    
    else:
        # Fallback to Qdrant (compatible with original behavior)
        from core.vector_stores.qdrant_store import QdrantVectorStore
        return QdrantVectorStore(collection_name=collection_name)
