import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.memory.ziva_memory import ZivaMemory
from qdrant_client import QdrantClient

def test_init():
    print("Initializing ZivaMemory...")
    # This should create the collections with 768 dims
    mem = ZivaMemory(embedding_dim=768) 
    
    client = QdrantClient(url="http://localhost:6333")
    collections = client.get_collections().collections
    
    found_quadrants = []
    for c in collections:
        if c.name.startswith("Q") or c.name == "episodic_memories":
            found_quadrants.append(c.name)
            
            # Check dimensions
            info = client.get_collection(c.name)
            dim = info.config.params.vectors.size
            print(f"✅ Collection {c.name}: {dim} dims")
            
            if dim != 768:
                print(f"❌ ERROR: {c.name} has {dim} dims, expected 768!")
    
    print(f"\nFound {len(found_quadrants)} memory collections.")

if __name__ == "__main__":
    test_init()
