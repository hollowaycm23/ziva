import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()
from core.llm import LLMService
from core.vector_store import VectorStore

llm = LLMService()
vs = VectorStore()

stats = vs.get_stats()
print(f"Total points: {stats.get('total_points', '?')}")

emb = llm.embedding("como fazer um hook em react")
results = vs.search(emb, limit=5)
for r in results:
    m = r["metadata"]
    print(f"  {r['score']:.3f} | {m.get('conceito','?'):40s} | cat={m.get('categoria','?'):20s} | nivel={m.get('nivel','?')}")
