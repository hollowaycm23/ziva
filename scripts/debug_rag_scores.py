#!/usr/bin/env python3
"""
Debug RAG Scores
Helper script to inspect vector scores and reranker scores for specific queries.
"""

import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.rag_helper import RAGHelper, get_reranker
from core.vector_store import VectorStore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DebugRAG")

def inspect_scores(query: str):
    logger.info(f"🔍 Analyzing Query: '{query}'")
    
    rag = RAGHelper()
    vs = VectorStore()
    reranker = get_reranker()
    
    # 1. Get Embedding
    embedding = rag.get_embedding(query)
    if not embedding:
        logger.error("❌ Failed to generate embedding")
        return

    # 2. Vector Search (Raw)
    logger.info("--- Vector Search Results (Top 10) ---")
    results = vs.search(embedding, limit=10)
    
    for i, res in enumerate(results):
        print(f"[{i}] Score: {res.get('score', 0):.4f} | Title: {res.get('payload', {}).get('title', 'N/A')[:50]}")

    # 3. Reranking
    if results:
        logger.info("\n--- Reranker Scores (Top 10) ---")
        reranked = reranker.rerank(query, results, top_k=10)
        
        for i, res in enumerate(reranked):
            score = res.get('score', 0)
            print(f"[{i}] BGE Score: {score:.4f} | Title: {res.get('payload', {}).get('title', 'N/A')[:50]}")
            
            # Sigmoid estimation just for reference
            import math
            try:
                sigmoid = 1 / (1 + math.exp(-score))
            except:
                sigmoid = 0.0
            print(f"    -> Sigmoid Prob: {sigmoid:.4f}")

if __name__ == "__main__":
    test_query = "Discuss strict confidentiality issues for SMEs in smart cities."
    if len(sys.argv) > 1:
        test_query = sys.argv[1]
        
    inspect_scores(test_query)
