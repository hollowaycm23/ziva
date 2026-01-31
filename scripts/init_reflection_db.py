
from core.reflection import ReflectionManager
import time

def init_db():
    print("Initializing Reflection DB (Bypassing LLM)...")
    # Initialize without LLM backend since we only test storage
    reflector = ReflectionManager(llm_backend="DUMMY") 
    
    # Mock Reflection
    dummy_reflection = {
        "score": 5,
        "success": True,
        "critique": "Initialization Test",
        "lesson": "Persistence works."
    }
    
    # Init client manually since we bypassed normal flow
    from qdrant_client import QdrantClient
    import os
    from core.llm import LLMService 
    
    url = os.getenv("QDRANT_URL", "http://localhost:6333")
    reflector.client = QdrantClient(url=url)
    reflector.collection_name = "evolutionary_reflections"
    reflector.embedder = LLMService(model="nomic-embed-text")
    
    print("Ensuring collection...")
    reflector._ensure_collection()
    
    print("Saving dummy reflection...")
    reflector.save_reflection(dummy_reflection, "Test Init", "Test Answer")
    print("Done.")

if __name__ == "__main__":
    init_db()
