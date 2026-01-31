import sys
import os
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    client = QdrantClient(url="http://localhost:6333")
    collection_name = "main_knowledge"

    print("🔍 Verificando se a Lição 01 foi aprendida...")

    try:
        scroll_filter = Filter(
            must=[
                FieldCondition(
                    key="source",
                    match=MatchValue(value="antigravity_tutor")
                )
            ]
        )

        points, _ = client.scroll(
            collection_name=collection_name,
            scroll_filter=scroll_filter,
            limit=100,
            with_payload=True
        )

        if not points:
            print("❌ Nenhuma lição do Tutor encontrada no Qdrant!")
        else:
            print(f"✅ Sucesso! Encontradas {len(points)} lições de Antigravity.")
            for p in points:
                print(f"\n--- ID: {p.id} ---")
                print(f"Topic: {p.payload.get('topic')}")
                print(f"Content: {p.payload.get('text')[:100]}...")
                print(f"Confidence: {p.payload.get('confidence')}")

    except Exception as e:
        print(f"Erro ao consultar Qdrant: {e}")

if __name__ == "__main__":
    main()
