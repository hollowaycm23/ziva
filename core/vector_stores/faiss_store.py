import os
import time
import uuid
import numpy as np
import faiss
from typing import List, Dict, Any, Optional
from core.vector_store_base import VectorStoreBase
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

# Custom class to bypass langchain embedding requirement since we provide vectors directly
class DirectEmbedding(Embeddings):
    def embed_query(self, text): 
        return []
    def embed_documents(self, texts): 
        return []

class FAISSVectorStore(VectorStoreBase):
    """
    Implementação do VectorStore usando FAISS com persistência local.
    """

    def __init__(self, collection_name="faiss_index", index_path=None):
        if index_path is None:
            index_path = os.getenv("FAISS_INDEX_PATH", "/home/holloway/ziva/data/faiss")
        
        self.index_path = os.path.join(index_path, collection_name)
        self.collection_name = collection_name
        self.vector_store = None
        self._load_or_create()

    def _load_or_create(self):
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        if os.path.exists(os.path.join(self.index_path, "index.faiss")):
            self.vector_store = FAISS.load_local(
                self.index_path, 
                DirectEmbedding(), 
                allow_dangerous_deserialization=True
            )
        else:
            dim = 768
            index = faiss.IndexFlatIP(dim)
            self.vector_store = FAISS(
                embedding_function=DirectEmbedding(),
                index=index,
                docstore=InMemoryDocstore({}),
                index_to_docstore_id={}
            )

    def add_text(self, text: str, embedding: List[float], metadata: Optional[Dict] = None) -> Optional[str]:
        if self.exists_similar(embedding):
            return None
        return self.add_texts([text], [embedding], [metadata])[0]

    def add_texts(self, texts: List[str], embeddings: List[List[float]], metadatas: Optional[List[Dict]] = None) -> List[str]:
        ids = [str(uuid.uuid4()) for _ in texts]
        
        docs = []
        for i, text in enumerate(texts):
            meta = {"timestamp": time.time(), "id": ids[i]}
            if metadatas and i < len(metadatas) and metadatas[i] is not None:
                meta.update(metadatas[i])
            docs.append(Document(page_content=text, metadata=meta))

        # Normalize and convert to float32
        embeddings_np = []
        for e in embeddings:
            vec = np.array(e, dtype=np.float32)
            faiss.normalize_L2(vec.reshape(1, -1))
            embeddings_np.append(vec.tolist())
            
        metadatas_list = [d.metadata for d in docs]
        
        # LangChain FAISS add_embeddings expects (text, embedding) pairs
        text_embeddings = list(zip(texts, embeddings_np))
        self.vector_store.add_embeddings(text_embeddings, metadatas=metadatas_list, ids=ids)
        
        self.vector_store.save_local(self.index_path)
        return ids

    def search(self, embedding: List[float], limit: int = 5, filters: Optional[Dict] = None, query_text: Optional[str] = None) -> List[Dict]:
        emb_np = np.array(embedding, dtype=np.float32)
        faiss.normalize_L2(emb_np.reshape(1, -1))
        
        # similarity_search_with_score_by_vector returns List[Tuple[Document, float]]
        results_with_scores = self.vector_store.similarity_search_with_score_by_vector(
            emb_np.tolist(), k=limit
        )

        formatted = []
        for doc, score in results_with_scores:
            formatted.append({
                "text": doc.page_content,
                "score": float(score),
                "metadata": doc.metadata
            })
        return formatted

    def scroll(self, limit: int = 100, offset: Any = None) -> tuple[List[Dict], Any]:
        # For FAISS, we can iterate over the docstore. 
        # offset will be the index in the list of keys.
        keys = list(self.vector_store.docstore._dict.keys())
        start_idx = int(offset) if offset is not None else 0
        end_idx = min(start_idx + limit, len(keys))
        
        batch_keys = keys[start_idx:end_idx]
        docs = []
        for k in batch_keys:
            doc = self.vector_store.docstore._dict[k]
            # Try to get vector if possible (though reconstruction might not match original exactly)
            vec = None
            try:
                # If we have index_to_docstore_id, we can find the position in the FAISS index
                # Reverse mapping search
                rev_map = {v: k_idx for k_idx, v in self.vector_store.index_to_docstore_id.items()}
                idx_pos = rev_map.get(k)
                if idx_pos is not None and hasattr(self.vector_store.index, 'reconstruct'):
                    vec = self.vector_store.index.reconstruct(int(idx_pos))
            except Exception:
                pass
            
            docs.append({
                "id": k,
                "text": doc.page_content,
                "vector": vec.tolist() if vec is not None else None,
                "metadata": doc.metadata
            })
        
        next_offset = end_idx if end_idx < len(keys) else None
        return docs, next_offset

    def exists_similar(self, embedding: List[float], threshold: float = 0.95) -> bool:
        results = self.search(embedding, limit=1)
        if results and results[0]["score"] >= threshold:
            return True
        return False

    def delete_old_points(self, days: int) -> int:
        cutoff = time.time() - (days * 86400)
        ids_to_delete = []
        
        # Iterate over docstore to find old IDs
        for k, doc in self.vector_store.docstore._dict.items():
            ts = doc.metadata.get("timestamp", 0)
            if ts < cutoff:
                ids_to_delete.append(k)
        
        if ids_to_delete:
            self.vector_store.delete(ids_to_delete)
            self.vector_store.save_local(self.index_path)
            return len(ids_to_delete)
        return 0

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_points": self.vector_store.index.ntotal,
            "backend": "FAISS",
            "path": self.index_path,
            "status": "Ready"
        }
