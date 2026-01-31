import logging
from typing import List, Dict
from sentence_transformers import CrossEncoder
import torch

logger = logging.getLogger("Reranker")


class Reranker:
    """
    Reranker for RAG pipeline using Cross-Encoders.
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-base",
                 device: str = None):
        """
        Initialize the Reranker.
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu" \
            if device is None else device

        logger.info(
            f"🔄 Initializing Reranker with {model_name} on {self.device}...")

        try:
            self.model = CrossEncoder(model_name, device=self.device)
            logger.info("✅ Reranker initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Reranker: {e}")
            self.model = None

    def rerank(self, query: str,
               documents: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        Rerank a list of documents based on the query.
        """
        if not self.model:
            logger.warning("Reranker model not loaded. Returning original.")
            return documents[:top_k]

        if not documents:
            return []

        valid_docs = []
        pairs = []

        for doc in documents:
            text = doc.get("text", "")
            if text:
                valid_docs.append(doc)
                pairs.append([query, text])

        if not pairs:
            return []

        try:
            scores = self.model.predict(pairs)
            
            # Normalizar scores (Logits -> Probabilidade) usando Sigmoid
            scores = torch.tensor(scores)
            probabilities = torch.sigmoid(scores).tolist()

            for i, score in enumerate(probabilities):
                valid_docs[i]['score'] = float(score)
                if 'metadata' not in valid_docs[i]:
                    valid_docs[i]['metadata'] = {}
                valid_docs[i]['metadata']['reranked'] = True

            valid_docs.sort(key=lambda x: x['score'], reverse=True)

            logger.info(
                f"⚡ Reranked {len(valid_docs)} documents. "
                f"Top score: {valid_docs[0]['score']:.4f}")

            return valid_docs[:top_k]

        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return documents[:top_k]


_reranker = None


def get_reranker() -> Reranker:
    global _reranker
    if _reranker is None:
        _reranker = Reranker()
    return _reranker