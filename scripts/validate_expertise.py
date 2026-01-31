#!/usr/bin/env python3
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.vector_store import VectorStore
from core.llm import LLMService

def main():
    store = VectorStore(collection_name="main_knowledge")
    llm = LLMService()
    
    queries = [
        "What are recent advances in quantum information?",
        "Explain neural network optimization"
    ]
    
    print("--- 🧠 VALIDATING EXPERTISE RETRIEVAL (FAST) ---")
    
    for q in queries:
        print(f"\n🔍 Query: '{q}'")
        emb = llm.embedding(q)
        # Search without active recall/rerank for speed
        results = store.search(embedding=emb, limit=5, use_active_recall=False)
        
        found_arxiv = False
        for r in results:
            meta = r.get("metadata", {})
            source = meta.get("source", "unknown")
            title = meta.get("title", "No Title")
            score = r.get("score", 0.0)
            
            print(f"   - [{source}] ({score:.2f}) {title}")
            
            if source == "arxiv":
                found_arxiv = True
        
        if found_arxiv:
            print("   ✅ Found ArXiv paper!")
        else:
            print("   ⚠️ No ArXiv paper found.")

if __name__ == "__main__":
    main()
