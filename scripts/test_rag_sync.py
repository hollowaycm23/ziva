#!/usr/bin/env python3
import sys
import os
import requests
import logging
from pathlib import Path

# Setup Path
sys.path.append(os.getcwd())

from core.p2p_learning import P2PLearningNode
from core.rag_helper import get_rag_helper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestRAGSync")

def test_rag_sync():
    print("🧪 Testando Sincronização RAG P2P...")
    
    # 1. Inserir um documento de teste no Qdrant local
    rag = get_rag_helper()
    test_text = "Ziva P2P Sync Test Document: 987654321"
    embedding = rag.get_embedding(test_text)
    
    if embedding:
        rag.vector_store.add_text(test_text, embedding, {
            "source": "sync_test",
            "type": "marker_doc"
        })
        print("✅ Documento marcador inserido no Qdrant local via RAGHelper.")
    else:
        print("❌ Falha ao gerar embedding para teste.")
        return

    # 2. Inicializar Nó P2P
    node = P2PLearningNode(node_name="test_ziva_sender")
    
    # 3. Executar Sync (Loopback para localhost:8000)
    # A API Ziva deve estar rodando em localhost:8000
    peer_url = "http://localhost:8005"
    
    print(f"\n🔄 Iniciando sync para {peer_url} (Loopback)...")
    success = node.sync_rag_knowledge(peer_url)
    
    if success:
        print("\n✅ Sync reportado como sucesso pelo cliente.")
    else:
        print("\n❌ Sync falhou.")

def main():
    # Verificar se API está online
    try:
        requests.get("http://localhost:8005/v1/health")
    except:
        print("⚠️  A API Ziva não parece estar rodando em http://localhost:8005")
        print("Por favor, inicie o './start.sh' em outro terminal antes de rodar este teste.")
        return

    test_rag_sync()

if __name__ == "__main__":
    main()
