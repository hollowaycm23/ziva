import sys
import os
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Setup
client = QdrantClient(url="http://localhost:6333")
collection_name = "main_knowledge"

def get_last_research():
    # Filter for web search summaries
    scroll_filter = models.Filter(
        must=[
            models.FieldCondition(
                key="source",
                match=models.MatchValue(value="legacy_web_cache")
            )
        ]
    )
    
    # Scroll (get a batch)
    # Since we don't have a reliable timestamp sort key in basic scroll, 
    # we might need to fetch many and sort python side, or rely on the Fact 
    # that IDs might be sequential-ish or we look for "web_search_cache" source.
    
    records, _ = client.scroll(
        collection_name=collection_name,
        scroll_filter=scroll_filter,
        limit=10,
        with_payload=True,
        with_vectors=False
    )
    
    if not records:
        print("Nenhuma pesquisa encontrada.")
        return

    print(f"Encontradas {len(records)} pesquisas. Exibindo a(s) mais recente(s):")
    
    # Try to sort if there is a timestamp in payload, else just show all
    # The payload likely has 'title' or 'content'.
    
    for record in records:
        print(f"\n--- ID: {record.id} ---")
        # Debug: print keys
        # print(f"Keys: {record.payload.keys()}")
        print(f"Title: {record.payload.get('title', 'No Title')}")
        print(f"Source: {record.payload.get('source', 'Unknown')}")
        # Try 'text' which is standard for VectorStore.add_text
        content = record.payload.get('text', record.payload.get('content', ''))
        print(f"Content: {content[:500]}...")

if __name__ == "__main__":
    get_last_research()
