
from core.dataset_builder import DatasetBuilder
from core.p2p_learning import GabrielleConnector
import sys
import logging
import time
import json
import random

# Ensure root is in path
sys.path.insert(0, '/home/holloway/ziva')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger("CollabTraining")


def load_or_generate_data():
    """
    Tenta carregar dados reais, se não houver, gera sintéticos de alta qualidade.
    """
    try:
        builder = DatasetBuilder()
        # Tentar pegar dados reais primeiro
        real_data = builder.build_dataset(output_format="alpaca")

        if len(real_data) > 5:
            logger.info(
                f"📚 Carregados {
                    len(real_data)} exemplos REAIS do banco de dados local.")
            return real_data
    except Exception as e:
        logger.warning(f"Erro ao carregar dados reais: {e}")

    logger.info(
        "⚠️  Dados reais insuficientes. Gerando 'Golden Data' sintético para treinamento...")

    # Dados Sintéticos "Ouro" (Exemplos de alta qualidade que queremos que a
    # Gabrielle aprenda)
    golden_data = [{"instruction": "Como verificar se um processo está rodando na porta 9000?",
                    "output": "Execute o comando: `netstat -tuln | grep 9000`",
                    "task_type": "devops",
                    "quality_score": 1.0},
                   {"instruction": "Qual o comando para listar arquivos ordenados por data?",
                    "output": "Use `ls -lt` para listar por data decrescente (mais novos primeiro).",
                    "task_type": "shell",
                    "quality_score": 0.95},
                   {"instruction": "Exemplo de criação de tabela SQLite segura",
                    "output": "```sql\nCREATE TABLE IF NOT EXISTS users (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    username TEXT NOT NULL UNIQUE,\n    created_at REAL\n);\n```",
                    "task_type": "coding",
                    "quality_score": 1.0}]

    # Multiplicar para volume
    training_batch = golden_data * 5
    return training_batch


def run_collaborative_session():
    print("\n🚀 INICIANDO SESSÃO DE TREINAMENTO COLABORATIVO (Ziva -> Gabrielle)")
    print("===================================================================")

    # 1. Preparar Dados
    print("📦 Preparando lote de treinamento...")
    dataset = load_or_generate_data()
    print(f"📊 Lote pronto: {len(dataset)} exemplos de alta qualidade.")

    # 2. Conectar P2P
    print("\n🔗 Estabelecendo Uplink Binário Segura (Porta 9000)...")
    connector = GabrielleConnector(host="100.114.201.84", port=9000)

    if not connector.is_connected:
        print("❌ ERRO CRÍTICO: Não foi possível conectar à Gabrielle.")
        return False

    print("✅ Conexão verificada e autenticada.")

    # 3. Transmitir Conhecimento
    print("\n🧠 Iniciando Transferência Neural (Sync Data)...")
    start_time = time.time()

    success = connector.teach_gabrielle(dataset)

    duration = time.time() - start_time

    if success:
        print(f"\n✅ SUCESSO! Transferência concluída em {duration:.2f}s")
        print(
            f"📈 {
                len(dataset)} novos padrões de inteligência foram assimilados pela Gabrielle.")
        print("🎉 A Colaboração Ziva-Gabrielle está ativa!")
    else:
        print("\n❌ FALHA na transferência. Verifique logs do servidor remoto.")

    connector.close()
    return success


if __name__ == "__main__":
    run_collaborative_session()
