import tarfile
import os
import shutil
import logging
from pathlib import Path

# Configuração
MEMORY_BACKUP_PATH = "/home/holloway/ziva/ziva_memory.tar.gz"
QDRANT_STORAGE_PATH = "/home/holloway/ziva/data/qdrant_storage"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RestoreMemory")


def restore_memory():
    """
    Restaura o backup da memória vetorial (Qdrant Snapshot).
    """
    backup = Path(MEMORY_BACKUP_PATH)
    if not backup.exists():
        logger.error(f"Backup não encontrado em: {MEMORY_BACKUP_PATH}")
        return

    logger.info("Iniciando restauração de memória...")

    # 1. Parar ou garantir que Qdrant não está escrevendo (Client local file based)
    # Como usamos Qdrant local, apenas garantir que não há processos ativos travando seria ideal.
    # Mas como é um script inicial, vamos supor safe.

    # 2. Extrair
    try:
        # Se o diretório já existe, talvez limpar ou fazer backup dele?
        # Por enquanto, vamos extrair por cima ou limpar se solicitado.
        # Vamos extrair em um temp e mover para garantir estrutura.

        extract_path = "/home/holloway/ziva/data/restore_temp"
        os.makedirs(extract_path, exist_ok=True)

        with tarfile.open(backup, "r:gz") as tar:
            tar.extractall(path=extract_path)

        logger.info(f"Backup extraído para {extract_path}")

        # Mover arquivos para o local correto
        # A estrutura do tar.gz depende de como foi criado. Assumindo que contem o conteudo de qdrant_storage
        # Se o tar contiver a pasta 'qdrant_storage', movemos o conteudo.

        # Vamos inspecionar o que foi extraído
        extracted_items = os.listdir(extract_path)
        source_dir = extract_path
        if "qdrant_storage" in extracted_items:
            source_dir = os.path.join(extract_path, "qdrant_storage")

        # Copiar/Mover para o destino final
        if os.path.exists(QDRANT_STORAGE_PATH):
            shutil.rmtree(QDRANT_STORAGE_PATH)

        shutil.copytree(source_dir, QDRANT_STORAGE_PATH)
        logger.info(f"Memória restaurada com sucesso em {QDRANT_STORAGE_PATH}")

        # Cleanup
        shutil.rmtree(extract_path)

    except Exception as e:
        logger.error(f"Erro ao restaurar backup: {e}")


if __name__ == "__main__":
    restore_memory()
