import logging
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from core.vector_store import VectorStore
from core.llm import LLMService
from core.database import DatabaseManager
from extensions.docstring_tools import standardize_docstrings
from core.config import config

logger = logging.getLogger("FileMonitor")


class CodeFileHandler(FileSystemEventHandler):
    """Handler para monitorar mudanças em arquivos de código"""

    def __init__(self):
        self.vs = VectorStore()
        self.llm = LLMService()
        self.db = DatabaseManager()
        self.extensions = {'.py', '.js', '.sh', '.md'}
        self.ignore_dirs = {
            '.venv',
            '__pycache__',
            'node_modules',
            '.git',
            'data/qdrant_storage_fixed'}

    def should_index(self, path):
        """Verifica se o arquivo deve ser indexado"""
        p = Path(path)

        # Verificar extensão
        if p.suffix not in self.extensions:
            return False

        # Verificar diretórios ignorados
        if any(ig in str(p) for ig in self.ignore_dirs):
            return False

        return True

    def index_file(self, file_path):
        """Indexa um arquivo no sistema de conhecimento"""
        try:
            p = Path(file_path)

            # Padronizar docstrings se for Python
            if p.suffix == '.py':
                logger.info(f"📝 Padronizando docstrings: {p.name}")
                try:
                    standardize_docstrings(str(p), auto_fix=True)
                except Exception as e:
                    logger.warning(f"Erro ao padronizar docstrings: {e}")

            content = p.read_text(encoding='utf-8', errors='ignore')

            # Dividir em chunks
            chunks = [content[i:i + 1000]
                      for i in range(0, len(content), 1000)]

            indexed = 0
            for idx, chunk in enumerate(chunks):
                emb_config = config.get_llm_provider("agent.embedding_model")
                model_name = emb_config["model_name"] if emb_config else "text-embedding-qwen2.5-0.5b-instruct"
                embedding = self.llm.embedding(chunk, model=model_name)

                if embedding:
                    metadata = {
                        "source": "auto_indexed",
                        "file": str(p),
                        "language": p.suffix[1:],
                        "chunk": idx
                    }

                    point_id = self.vs.add_text(chunk, embedding, metadata)

                    if point_id:
                        conn = self.db._get_conn()
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT OR REPLACE INTO code_index "
                            "(file_path, chunk_id, content, language, "
                            "indexed_at) VALUES (?, ?, ?, ?, ?)",
                            (str(p), f"{p.name}_{idx}",
                             chunk, p.suffix[1:], time.time())
                        )
                        conn.commit()
                        conn.close()
                        indexed += 1

            logger.info(f"✅ Auto-indexado: {p.name} ({indexed} chunks)")

        except Exception as e:
            logger.error(f"Erro ao indexar {file_path}: {e}")

    def on_created(self, event):
        """Arquivo criado"""
        if not event.is_directory and self.should_index(event.src_path):
            logger.info(f"📄 Novo arquivo detectado: {event.src_path}")
            time.sleep(1)  # Aguardar arquivo ser escrito completamente
            self.index_file(event.src_path)

    def on_modified(self, event):
        """Arquivo modificado"""
        if not event.is_directory and self.should_index(event.src_path):
            logger.info(f"✏️  Arquivo modificado: {event.src_path}")
            time.sleep(1)
            self.index_file(event.src_path)


def start_file_monitor(directory="/home/holloway/ziva"):
    """Inicia o monitoramento de arquivos"""
    event_handler = CodeFileHandler()
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=True)
    observer.start()

    logger.info(f"👁️  Monitoramento de arquivos iniciado em {directory}")

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == "__main__":
    start_file_monitor()
