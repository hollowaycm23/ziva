import os
import time
import uuid
from typing import List, Dict, Any, Optional
from core.vector_store_base import VectorStoreBase
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

class ElasticsearchVectorStore(VectorStoreBase):
    """
    Implementação do VectorStore usando Elasticsearch.
    Suporta busca híbrida (Vetor + BM25).
    """

    def __init__(self, collection_name="ziva_knowledge", es_url=None):
        if es_url is None:
            es_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        
        self.client = Elasticsearch(es_url)
        self.index_name = collection_name
        
        # Pesos para busca híbrida (configuráveis via .env)
        self.knn_boost = float(os.getenv("ZIVA_ES_KNN_BOOST", "0.7"))
        self.bm25_boost = float(os.getenv("ZIVA_ES_BM25_BOOST", "0.3"))
        
        self._init_index()

    def _init_index(self):
        if not self.client.indices.exists(index=self.index_name):
            # Define mapping for hybrid search
            mapping = {
                "mappings": {
                    "properties": {
                        "text": {"type": "text"}, # For BM25
                        "vector": {
                            "type": "dense_vector",
                            "dims": 768,
                            "index": True,
                            "similarity": "cosine"
                        },
                        "metadata": {"type": "object"},
                        "timestamp": {"type": "date"}
                    }
                }
            }
            self.client.indices.create(index=self.index_name, body=mapping)

    def add_text(self, text: str, embedding: List[float], metadata: Optional[Dict] = None) -> Optional[str]:
        if self.exists_similar(embedding):
            return None
        
        point_id = str(uuid.uuid4())
        doc = {
            "text": text,
            "vector": embedding,
            "metadata": metadata or {},
            "timestamp": time.time() * 1000 # ES uses ms
        }
        self.client.index(index=self.index_name, id=point_id, document=doc, refresh=True)
        return point_id

    def add_texts(self, texts: List[str], embeddings: List[List[float]], metadatas: Optional[List[Dict]] = None) -> List[str]:
        actions = []
        ids = []
        for i, text in enumerate(texts):
            point_id = str(uuid.uuid4())
            doc = {
                "_index": self.index_name,
                "_id": point_id,
                "text": text,
                "vector": embeddings[i],
                "metadata": metadatas[i] if metadatas and i < len(metadatas) else {},
                "timestamp": time.time() * 1000
            }
            actions.append(doc)
            ids.append(point_id)
        
        bulk(self.client, actions, refresh=True)
        return ids

    def search(self, embedding: List[float], limit: int = 5, filters: Optional[Dict] = None, query_text: Optional[str] = None) -> List[Dict]:
        """
        Busca Híbrida: kNN (vetores) + Rank Fusion com Match (BM25).
        """
        # Base query structure for ES 8.x
        search_query = {
            "knn": {
                "field": "vector",
                "query_vector": embedding,
                "k": limit,
                "num_candidates": 100,
                "boost": self.knn_boost
            }
        }

        # Adiciona busca por texto se fornecido
        if query_text:
            search_query["query"] = {
                "bool": {
                    "should": [
                        {"match": {"text": {"query": query_text, "boost": self.bm25_boost}}}
                    ]
                }
            }
        
        # Filtros (opcional)
        if filters:
            search_query["knn"]["filter"] = filters

        resp = self.client.search(index=self.index_name, body=search_query, size=limit)
        
        formatted = []
        for hit in resp['hits']['hits']:
            formatted.append({
                "text": hit['_source']['text'],
                "score": hit['_score'],
                "metadata": hit['_source']['metadata']
            })
        return formatted

    def scroll(self, limit: int = 100, offset: Any = None) -> tuple[List[Dict], Any]:
        # ES uses search_after for large scrolls, but for simple migration 
        # we can use the 'from' parameter or 'scroll' API.
        if offset is None:
            resp = self.client.search(
                index=self.index_name,
                body={"query": {"match_all": {}}},
                scroll="1m",
                size=limit
            )
        else:
            resp = self.client.scroll(scroll_id=offset, scroll="1m")

        scroll_id = resp.get('_scroll_id')
        hits = resp['hits']['hits']
        
        docs = []
        for hit in hits:
            docs.append({
                "id": hit['_id'],
                "text": hit['_source']['text'],
                "vector": hit['_source'].get('vector'),
                "metadata": hit['_source']['metadata']
            })
            
        # Limpar scroll se não houver mais nada
        if not hits and scroll_id:
            try:
                self.client.clear_scroll(scroll_id=scroll_id)
            except Exception:
                pass
            scroll_id = None
            
        return docs, scroll_id

    def exists_similar(self, embedding: List[float], threshold: float = 0.95) -> bool:
        results = self.search(embedding, limit=1)
        if results and results[0]["score"] >= threshold:
            return True
        return False

    def delete_old_points(self, days: int) -> int:
        cutoff_ms = (time.time() - (days * 86400)) * 1000
        query = {
            "query": {
                "range": {
                    "timestamp": {"lt": cutoff_ms}
                }
            }
        }
        try:
            resp = self.client.delete_by_query(index=self.index_name, body=query, refresh=True)
            return resp.get("deleted", 0)
        except Exception as e:
            print(f"Error deleting old points from ES: {e}")
            return -1

    def get_stats(self) -> Dict[str, Any]:
        try:
            stats = self.client.indices.stats(index=self.index_name)
            return {
                "total_points": stats['indices'][self.index_name]['total']['docs']['count'],
                "backend": "Elasticsearch",
                "status": "Ready"
            }
        except Exception as e:
            return {"error": str(e)}
