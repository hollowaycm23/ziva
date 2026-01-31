from core.llm import LLMService
import logging

logging.basicConfig(level=logging.INFO)

def test():
    print("Initializing LLMService...")
    embedder = LLMService(model="nomic-embed-text:latest")
    
    print(f"Checking if running: {embedder.is_running()}")
    
    questions = ["qual ave pode voar de costas", "test query"]
    
    for q in questions:
        print(f"Embedding: '{q}'")
        vec = embedder.embedding(q)
        if vec:
            print(f"✅ Vector extracted. Length: {len(vec)}")
            print(f"First 5 dims: {vec[:5]}")
        else:
            print("❌ Failed to extract vector.")

if __name__ == "__main__":
    test()
