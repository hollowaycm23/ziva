from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

client = QdrantClient(url="http://localhost:6333")

try:
    print("Clearing staging_sync...")
    client.delete_collection("staging_sync")
    print("Clearing main_knowledge...")
    client.delete_collection("main_knowledge")
    print("Deleted. Logic will recreate them on next run.")
except Exception as e:
    print(e)
