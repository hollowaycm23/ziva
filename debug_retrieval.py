import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from qdrant_client import QdrantClient
from core.llm import LLMService

def debug_magno_retrieval():
    print("🧠 Debugging Retrieval for 'Magno Fernando Fonseca'...")
    
    # Init services
    client = QdrantClient(url="http://localhost:6333")
    llm = LLMService()
    
    collection = "main_knowledge"
    query = "quem e Magno Fernando Fonseca"
    
    print(f"Query: {query}")
    
    # 1. Generate Embedding
    vec = llm.embedding(query, model="nomic-embed-text")
    if not vec:
        print("❌ Embedding generation failed!")
        return
        
    # 2. Search
    print("Searching in Qdrant (limit=20)...")
    response = client.query_points(
        collection_name=collection,
        query=vec,
        limit=20,
        with_payload=True
    )
    results = response.points
    
    found_lesson = False
    for i, res in enumerate(results):
        text = res.payload.get("text", "No text")
        is_magno = "Magno" in text
        mark = "✅" if is_magno else "  "
        print(f"{i+1:02d}. [{res.score:.4f}] {mark} {text[:80]}...")
        
        if is_magno:
            found_lesson = True
            
    if not found_lesson:
        print("\n❌ CRITICAL: 'Magno' lesson NOT found in top 20 results!")
        print("Possible causes:")
        print("1. Lesson was not indexed correctly (check 'core/sync_manager.py')")
        print("2. Embedding model mismatch (check 'receive_mentoring.py')")
        print("3. Collection dimensionality mismatch (should be 768)")
    else:
        print("\n✅ Lesson IS in the recall list. The Agent might be filtering it out.")

if __name__ == "__main__":
    debug_magno_retrieval()
