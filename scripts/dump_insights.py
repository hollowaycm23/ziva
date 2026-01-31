import sys
import os
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    client = QdrantClient(url="http://localhost:6333")
    # Check staging
    collection_name = "staging_sync"

    print(f"Querying collection '{collection_name}' for self-learning insights...")

    print(f"Querying collection '{collection_name}' for ALL points to debug...")

    try:
        # Scroll through all results (no filter)
        points, next_page_offset = client.scroll(
            collection_name=collection_name,
            limit=50,
            with_payload=True,
            with_vectors=False
        )
        
        print(f"Found {len(points)} total points (showing last 50):")

        for p in points:
            payload = p.payload
            text = payload.get('text', 'No text')
            source = payload.get('source', 'No source')
            job_id = payload.get('origin_job', 'N/A')
            
            print(f"--- ID: {p.id} | Source: {source} ---")
            print(f"Text: {text.strip()[:200]}...") # Truncate for readability
            print(f"Full Payload: {payload}")
            print("-" * 40)


    except Exception as e:
        print(f"Error querying Qdrant: {e}")

if __name__ == "__main__":
    main()
