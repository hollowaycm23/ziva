#!/usr/bin/env python3
from core.p2p_learning import GabrielleConnector
import sys
import os
import logging
import time

# Ensure root is in path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [SYNC] - %(message)s')
logger = logging.getLogger("SyncGabrielle")


def sync_gabrielle():
    print("\n🔗 Iniciando Sincronização com Gabrielle (HTTP Protocol)...")
    print("=========================================================")

    # Configuração de Peers (HTTP API)
    # Tenta conectar na API Rest da Gabrielle (Porta 8000)
    target_peer = "http://100.114.201.84:8000"

    from core.p2p_learning import P2PLearningNode

    # Inicializa Nó (Ziva)
    node = P2PLearningNode(node_name="node_07", peers=[target_peer])

    print(f"📡 Peer alvo: {target_peer}")

    # Executa Sincronização via HTTP (Share + Receive)
    try:
        print("\n🔄 Processando Sincronização Bidirecional...")
        node.sync_with_peers()
        print("✅ Sincronização concluída (logs detalhados em ziva_system.log)")

    except Exception as e:
        print(f"❌ Erro durante sincronização HTTP: {e}")
        print("💡 Dica: Verifique se a API da Gabrielle (Porta 8000) está acessível.")

    print("\n✨ Fim.")


if __name__ == "__main__":
    sync_gabrielle()
