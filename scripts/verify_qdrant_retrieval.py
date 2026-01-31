#!/usr/bin/env python3
import logging
from qdrant_client import QdrantClient
from core.llm import LLMService

# Configure logging to see ZivaLLM errors
logging.basicConfig(level=logging.DEBUG)

client = QdrantClient(host="localhost", port=6333)
collections = ["ziva_knowledge", "main_knowledge", "gabrielle_knowledge"]
query = "Qual é a única ave que consegue voar para trás?"

print(f"Buscando por: {query}")

# Precisamos do embedding
# Instantiate LLMService
llm = LLMService(model="nomic-embed-text")

# Debug: Print API Config
print(f"API Base: {llm.api_base}")
print(f"Model: {llm.model}")

vector = llm.embedding(query)

if not vector:
    print("Erro ao gerar embedding")
    exit(1)

for col in collections:
    print(f"\n--- Coleção: {col} ---")
    try:
        results = client.query_points(
            collection_name=col,
            query=vector,
            limit=5,
            with_payload=True
        ).points
        
        if not results:
            print("Nenhum resultado.")
            continue
            
        for hit in results:
            text = hit.payload.get("text", "")[:100]
            print(f"Score: {hit.score:.4f} | ID: {hit.id} | Text: {text}...")
            
    except Exception as e:
        print(f"Erro ao buscar na coleção {col}: {e}")
