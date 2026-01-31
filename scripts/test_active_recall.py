from core.rag_helper import RAGHelper
import sys
import os
import logging
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Configure Logging to see the "Active Recall triggered" message
logging.basicConfig(level=logging.INFO)


def test_recall():
    rag = RAGHelper()

    # 1. Insert a Dummy Lesson
    test_text = "LESSON: Always use HTTPS in production environments. EXAMPLE: protecting user data in transit."
    # Generate embedding
    embedding = rag.get_embedding(test_text)

    if not embedding:
        print("❌ Failed to generate embedding. Is Ollama running?")
        return

    # Add to store with special metadata
    rag.vector_store.add_text(
        text=test_text,
        embedding=embedding,
        metadata={"type": "learned_lesson", "source": "thought_police"}
    )
    print("✅ Dummy Lesson Injected.")

    # 2. Search for it
    query = "How to prevent SQL injection?"
    print(f"\n🔎 Searching for: '{query}'")

    results = rag.search_memories(query, limit=5)

    found = False
    for res in results:
        meta = res.get('metadata', {})
        score = res.get('score', 0)
        text = res.get('text', '')

        print(f"   - [{score:.4f}] {text[:60]}... (Type: {meta.get('type')})")

        if meta.get('type') == 'learned_lesson':
            found = True
            if score > 1.0:  # Cosine similarity is usually <= 1.0. If boosted, it can go higher.
                print("   ✨ BOOSTED SCORE DETECTED! Active Recall Working.")
            else:
                print(
                    "   ⚠️ Found, but score seems normal. Boost might be subtle or original score was low.")

    if found:
        print("\n✅ Test Passed: Lesson retrieved.")
    else:
        print("\n❌ Test Failed: Lesson not retrieved.")


if __name__ == "__main__":
    test_recall()
