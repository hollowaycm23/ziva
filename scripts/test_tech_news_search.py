from core.llm import LLMService
from core.vector_store import VectorStore
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


llm = LLMService(model="nomic-embed-text:latest")
vs = VectorStore()

query = "fontes de notícias de tecnologia"
print(f"Buscando: '{query}'")
print("=" * 80)

emb = llm.embedding(query)
results = vs.search(embedding=emb, limit=3)

for i, r in enumerate(results, 1):
    print(f"\n{i}. Score: {r['score']:.4f}")
    print(f"   Source: {r['metadata'].get('source', 'unknown')}")
    print(f"   Text preview: {r['text'][:300]}...")
