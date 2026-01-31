import os
import sys
import logging
from datetime import datetime

# Garantir que o diretório base está no path
sys.path.append(os.getcwd())

from scripts.migrate_vector_store import migrate

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("auto_sync.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AutoSync")

def run_auto_sync():
    """
    Executa a sincronização automática baseada no arquivo .env
    """
    source = os.getenv("SYNC_SOURCE", "faiss")
    target = os.getenv("SYNC_TARGET", "qdrant")
    source_coll = os.getenv("SYNC_SOURCE_COLL", "main_knowledge")
    target_coll = os.getenv("SYNC_TARGET_COLL", "main_knowledge")
    retention = os.getenv("SYNC_RETENTION")
    retention = int(retention) if retention else None
    
    logger.info(f"🔄 Iniciando Auto-Sync: {source} -> {target}")
    
    try:
        migrate(source, target, source_coll, target_coll, retention=retention)
        logger.info("✅ Auto-Sync concluído com sucesso.")
    except Exception as e:
        logger.error(f"❌ Falha no Auto-Sync: {e}")

if __name__ == "__main__":
    run_auto_sync()
