from qdrant_client import QdrantClient

def reset_collections():
    client = QdrantClient(url="http://localhost:6333")
    
    collections_to_reset = [
        "episodic_memories",
        "Q1_LOGIC",
        "Q2_USER_DATA",
        "Q3_PROJECTS",
        "Q4_ARCHIVE",
        "Q5_SKILLS",
        "Q6_CONVERSATIONS"
    ]
    
    print("WARNING: This will delete the following collections to enforce new 768-dim schema:")
    for c in collections_to_reset:
        print(f"- {c}")
    
    print("\nProceeding with deletion...")
    
    for collection in collections_to_reset:
        try:
            if client.collection_exists(collection):
                client.delete_collection(collection)
                print(f"✅ Deleted {collection}")
            else:
                print(f"⚠️ {collection} does not exist (skipping)")
        except Exception as e:
            print(f"❌ Error deleting {collection}: {e}")

    print("\nAll target collections cleared. They will be recreated with correct dimensions on next usage.")

if __name__ == "__main__":
    reset_collections()
