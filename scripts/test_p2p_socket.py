
from core.p2p_learning import GabrielleConnector
import sys
import logging
import time

# Ensure root is in path
sys.path.insert(0, '/home/holloway/ziva')

# Configure logging
logging.basicConfig(level=logging.INFO)


def test_binary_p2p():
    print("🚀 Iniciando Teste de Protocolo Binário (Socket 9000)...")

    # 1. Connect & Auth
    connector = GabrielleConnector(host="100.114.201.84", port=9000)

    if connector.is_connected:
        print("✅ Conexão Binária Estabelecida e Autenticada!")

        # 2. Test PING
        print("🔄 Testando Heartbeat (PING)...")
        if connector.health_check():
            print("✅ PONG recebido! Canal vivo.")
        else:
            print("❌ Falha no PING.")
            return False

        # 3. Test SYNC_DATA
        print("📤 Testando Envio de Dados (SYNC_DATA)...")
        dummy_dataset = [
            {
                "instruction": "Test instruction",
                "output": "Test output",
                "task_type": "verification",
                "quality_score": 1.0
            }
        ]

        if connector.teach_gabrielle(dummy_dataset):
            print("✅ Dados enviados e confirmados (ACK recebido)!")
            connector.close()
            return True
        else:
            print("❌ Falha no envio de dados.")
            connector.close()
            return False

    else:
        print("❌ Falha na conexão Binária. Verifique logs.")
        return False


if __name__ == "__main__":
    test_binary_p2p()
