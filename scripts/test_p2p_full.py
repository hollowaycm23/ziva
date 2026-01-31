
from core.p2p_learning import GabrielleConnector, P2PLearningNode
import sys
import logging
# Ensure root is in path
sys.path.insert(0, '/home/holloway/ziva')

# Configure logging
logging.basicConfig(level=logging.INFO)


def test_full_p2p():
    print("🚀 Iniciando Teste Completo de Sincronização P2P (HTTP/8000)...")

    # URL Direta (Bypass DNS)
    gabrielle_url = "http://100.114.201.84:8000"

    print(f"📡 Conectando a {gabrielle_url}...")
    connector = GabrielleConnector(gabrielle_url=gabrielle_url)

    if connector.is_connected:
        print("✅ Conexão HTTP Estabelecida!")

        # Testar obtenção de conhecimento
        print("🧠 Solicitando base de conhecimento remota...")
        knowledge = connector.get_gabrielle_knowledge()
        print(f"📚 Dados recebidos: {len(knowledge)} exemplos")

        # Simular node completo
        node = P2PLearningNode(node_name="ziva_local", peers=[gabrielle_url])

        # Tentar sync completo
        print("🔄 Executando ciclo de sincronização bidirecional...")
        try:
            node.sync_with_peers()
            print("✅ Sincronização concluída com sucesso!")
            return True
        except Exception as e:
            print(f"❌ Erro na sincronização: {e}")
            return False

    else:
        print(
            "❌ Falha na conexão HTTP. Verifique se a API remota está rodando na porta 8000.")
        return False


if __name__ == "__main__":
    test_full_p2p()
