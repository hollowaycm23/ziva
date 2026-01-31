from flashrank import Ranker, RerankRequest
import logging

import os
logger = logging.getLogger("ZivaRerank")
if os.getenv("ZIVA_VERBOSE", "false").lower() == "true":
    logger.setLevel(logging.INFO)
else:
    logger.setLevel(logging.WARNING)

# Initialize Ranker (Defaults to ms-marco-TinyBERT-L-2-v2 which is very fast ~40MB)
# We instantiate globally to avoid loading model on every request
try:
    ranker = Ranker()
except Exception as e:
    logger.error(f"Failed to initialize FlashRank: {e}")
    ranker = None

def rerank_documents(query: str, documents: list[str], top_k: int = 5) -> list[str]:
    """
    Reranks a list of document strings based on the query using a Cross-Encoder.
    
    Args:
        query: The user's query string.
        documents: A list of document contents (strings).
        top_k: Number of top documents to return.

    Returns:
        A list of the top_k sorted documents.
    """
    if not ranker or not documents:
        return documents[:top_k]

    try:
        # FlashRank expects a specific JSON-like structure
        passages = [
            {"id": i, "text": doc} 
            for i, doc in enumerate(documents)
        ]

        rerank_request = RerankRequest(query=query, passages=passages)
        results = ranker.rerank(rerank_request)

        # Sort based on score (FlashRank usually returns sorted, but good to be safe)
        # However, ranker.rerank returns a list of dictionaries with 'score' key
        # We need to map back to the original text
        
        # The result objects have 'id', 'text', 'score', 'meta'
        sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
        
        top_docs = [res['text'] for res in sorted_results[:top_k]]
        
        logger.info(f"Reranked {len(documents)} docs -> Top {len(top_docs)}")
        return top_docs

    except Exception as e:
        logger.error(f"Reranking error: {e}")
        # Fallback to original order
        return documents[:top_k]
