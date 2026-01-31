
from core.dataset_builder import DatasetBuilder
from core.p2p_learning import GabrielleConnector
import sys
import logging
import time

# Ensure root is in path
sys.path.insert(0, '/home/holloway/ziva')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s')


def run_full_sync():
    print("\n🚀 Sincronização Bidirecional Completa (Ziva <-> Gabrielle)")
    print("=========================================================")

    connector = GabrielleConnector(host="100.114.201.84", port=9000)

    if not connector.is_connected:
        print("❌ Falha na conexão.")
        return

    # 1. PUSH (Ziva -> Gabrielle)
    print("\n📤 [PUSH] Enviando conhecimento (Ziva -> Gabrielle)...")
    push_data = [
        {"instruction": "Teste Bidirecional Push", "output": "Sucesso",
            "task_type": "test", "quality_score": 1.0}
    ]
    if connector.teach_gabrielle(push_data):
        print("✅ PUSH realizado com sucesso.")
    else:
        print("❌ Falha no PUSH.")

    # 2. PULL (Gabrielle -> Ziva)
    print("\n📥 [PULL] Coletando conhecimento (Gabrielle -> Ziva)...")
    server_data = connector.get_gabrielle_knowledge()

    if server_data and len(server_data) > 0:
        print(
            f"✅ PULL processado com sucesso! Recebidos {
                len(server_data)} itens.")
        print("Exemplo recebido:", server_data[0]['instruction'])
    else:
        print("⚠️  PULL retornou 0 itens (ou falhou).")

    connector.close()


if __name__ == "__main__":
    run_full_sync()
