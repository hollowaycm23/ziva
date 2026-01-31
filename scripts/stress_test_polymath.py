#!/usr/bin/env python3
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.vector_store import VectorStore
from core.llm import LLMService

def main():
    store = VectorStore(collection_name="main_knowledge")
    llm = LLMService()
    
    tests = [
        {
            "name": "Self-Reflection (Code)",
            "query": "How does the Go Runtime enforce filesystem security and allowlisting?",
            "expected_keywords": ["server.go", "validatePath", "CommandWhitelist", "shell.go"]
        },
        {
            "name": "Polymath (Physics)",
            "query": "Summarize recent advances in Quantum Information from the ingested papers.",
            "expected_keywords": ["Carlo Novero", "Quantum Information", "experiments", "INRIM"]
        }
    ]
    
    print("--- 🧠 ZIVA POLYMATH STRESS TEST ---")
    
    for test in tests:
        print(f"\n[TEST] {test['name']}")
        print(f"Query: {test['query']}")
        
        emb = llm.embedding(test['query'])
        results = store.search(embedding=emb, limit=3, use_active_recall=False)
        
        passed = False
        print("  Retrieval Results:")
        for r in results:
            meta = r.get("metadata", {})
            title = meta.get("title") or meta.get("file_path") or "Unknown"
            source = meta.get("source", "unknown")
            text_snippet = r.get("text")[:100].replace("\n", " ")
            
            print(f"  - [{source}] {title}: {text_snippet}...")
            
            # Use strict keyword check from metadata or text
            full_text = f"{title} {source} {r.get('text')}"
            
            hits = [k for k in test['expected_keywords'] if k.lower() in full_text.lower()]
            if hits:
                print(f"    ✅ Hit keyword: {hits}")
                passed = True
                
        if passed:
            print(f"✅ {test['name']} PASSED.")
        else:
            print(f"❌ {test['name']} FAILED (Relevant docs not found).")
            
if __name__ == "__main__":
    main()
