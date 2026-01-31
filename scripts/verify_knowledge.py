from core.tools.fact_checker import FactChecker
from core.llm import LLMService
from core.vector_store import VectorStore
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def verify_and_update_knowledge():
    """
    Verifies existing knowledge in Qdrant and updates confidence scores.
    """
    print("🔍 Starting Fact-Checking Process...")

    llm = LLMService(model="nomic-embed-text:latest")
    vs = VectorStore()
    checker = FactChecker()

    # Example: Verify the hummingbird backward flight claim
    test_claims = [
        "O beija-flor é a única ave que pode voar para trás",
        "Galinhas podem atingir velocidade de 14,5 km/h em voo"
    ]

    for claim in test_claims:
        print(f"\n📋 Claim: {claim}")
        print("-" * 80)

        # Search for this claim in Qdrant
        emb = llm.embedding(claim)
        results = vs.search(embedding=emb, limit=1)

        if not results:
            print("  ⚠️ Claim not found in database")
            continue

        result = results[0]
        print(f"  📊 Current score: {result['score']:.4f}")
        print(f"  📝 Source: {result['metadata'].get('source', 'unknown')}")

        # Verify claim against external sources
        verification = checker.verify_claim(claim, max_sources=2)

        if verification["verified"]:
            confidence = verification["confidence"]
            print(f"  ✅ Verified! Confidence: {confidence:.2%}")
            print(f"  📚 Sources checked: {verification['sources_count']}")

            # Note: We would need the point_id to update
            # This is a demonstration of the concept
            print(f"  💾 Would update confidence to: {confidence:.2f}")
        else:
            print(f"  ❌ Could not verify: {verification['reason']}")


if __name__ == "__main__":
    verify_and_update_knowledge()
