import os
import sys

# Force VERBOSE for this script to see what's happening
os.environ["ZIVA_VERBOSE"] = "true"

# Adjust path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.vector_store import VectorStore
from core.llm import LLMService

# Instantiate directly
vs = VectorStore(collection_name="main_knowledge")
embedder = LLMService(model="nomic-embed-text:latest")

def check_knowledge(term):
    print(f"\n🔍 Diagnosing term: '{term}'")
    
    # 1. Check raw search
    vec = embedder.embedding(term)
    if not vec:
        print("❌ Embedding failed (Model issue?)")
        return

    results = vs.search(embedding=vec, limit=5)
    
    if not results:
        print("❌ No results found in Qdrant.")
    else:
        print(f"✅ Found {len(results)} matches.")
        for i, r in enumerate(results):
            score = r.get('score', 0)
            text = r.get('text', '')[:100].replace('\n', ' ')
            source = r.get('payload', {}).get('source', 'Unknown')
            print(f"   {i+1}. [{score:.4f}] {text}... (Source: {source})")
            
            # Check for our injected tags
            if "MEMÓRIA EPISÓDICA" in text or "manual_instruction" in source:
                print("      🌟 TARGET KNOWLEDGE FOUND!")

def check_id(point_id):
    print(f"\n🔍 Checking Point ID: {point_id}")
    try:
        points = vs.client.retrieve(collection_name="main_knowledge", ids=[point_id])
        if points:
            print(f"✅ Point Found! Text preview: {points[0].payload['text'][:50]}...")
        else:
            print("❌ Point NOT found by ID.")
    except Exception as e:
        print(f"❌ Error retrieving ID: {e}")

print("--- ZIVA DIAGNOSTIC TOOL ---")
print("Evaluating Memory State...")
check_knowledge("Pikas biology animal context")
check_id("8fbb2eed-0e04-4632-9d74-218f19f58e98")
check_knowledge("what is the 3 body problem formula")
check_knowledge("qual a formula da teoria dos 3 corpos")
