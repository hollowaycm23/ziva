from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

def clean_kb():
    client = QdrantClient(url="http://localhost:6333")
    
    # Nuke Main
    nuke_collection(client, "main_knowledge")
    # Nuke Staging
    nuke_collection(client, "staging_sync")
    
    return

    # Old logic below skipped...
    collection = "main_knowledge"
    
    # 1. Check Info
    try:
        info = client.get_collection(collection)
        print(f"Collection '{collection}':")
        print(f" - Status: {info.status}")
        print(f" - Points: {info.points_count}")
        print(f" - Vector Size: {info.config.params.vectors.size}")
    except Exception as e:
        print(f"❌ Error getting info: {e}")
        return

    # 2. Delete non-tutor content
    print("\nDeleting content where source != 'antigravity_tutor'...")
    
    # Filter for NOT match source='antigravity_tutor'
    # Actually Qdrant delete logic is easier by filtering what we want to DELETE.
    # We want to delete entries that do NOT have source 'antigravity_tutor'.
    # Or simpler: Delete everything that has source='web_search' or source='scraped'.
    # Since we don't know all sources, let's look at a few points.
    
    res = client.scroll(collection_name=collection, limit=10)
    sources = set()
    for p in res[0]:
        sources.add(p.payload.get("source", "unknown"))
    print(f"Found sources in sample: {sources}")
    
    # Delete points where source is NOT antigravity_tutor
    # We can do this by scrolling and deleting by ID if filter is hard.
    
    deleted_count = 0
    next_offset = None
    
    while True:
        points, next_offset = client.scroll(
            collection_name=collection,
            limit=100,
            with_payload=True,
            offset=next_offset
        )
        
        # NUKE EVERYTHING 
        ids_to_delete = [p.id for p in points]
        
        if ids_to_delete:
            client.delete(
                collection_name=collection,
                points_selector=ids_to_delete
            )
            deleted_count += len(ids_to_delete)
            print(f"Deleted {len(ids_to_delete)} points (NUKE)...")
            
        if not next_offset:
            break
            
    print(f"\n✅ Cleanup complete. Deleted {deleted_count} points from {collection}.")
    
def nuke_collection(client, collection):
    print(f"\n☢️ NUKING '{collection}'...")
    try:
        client.delete_collection(collection)
        print("✅ Collection deleted.")
        # Recreate empty to avoid errors
        from qdrant_client.models import VectorParams, Distance
        client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
        )
        print("✅ Collection recreated empty.")
    except Exception as e:
        print(f"⚠️ Error nuking {collection}: {e}")
    
    # Re-check count
    info = client.get_collection(collection)
    print(f"Remaining Points: {info.points_count}")

if __name__ == "__main__":
    clean_kb()
