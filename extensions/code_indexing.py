import logging
import time
from pathlib import Path
from agent.tools import ziva_tool
from core.vector_store import VectorStore
from core.llm import LLMService
from core.database import DatabaseManager

logger = logging.getLogger("CodeIndexing")


@ziva_tool
def index_codebase(directory: str = "/home/holloway/ziva",
                   extensions: str = ".py,.js,.sh") -> str:
    """
    Indexa código-fonte do projeto no sistema de conhecimento vetorial.

    Args:
        directory (str): Diretório raiz para indexar (default: projeto Ziva)
        extensions (str): Extensões separadas por vírgula (default: .py,.js,.sh)

    Returns:
        str: Relatório de indexação
    """
    try:
        vs = VectorStore()
        llm = LLMService()
        db = DatabaseManager()

        exts = [ext.strip() for ext in extensions.split(',')]
        base_path = Path(directory)

        indexed = 0
        skipped = 0
        errors = 0

        # Buscar arquivos
        files = []
        for ext in exts:
            files.extend(base_path.rglob(f'*{ext}'))

        # Filtrar diretórios ignorados
        ignore_dirs = {
            '.venv',
            '__pycache__',
            'node_modules',
            '.git',
            'data/qdrant_storage_fixed'}
        files = [f for f in files if not any(
            ig in str(f) for ig in ignore_dirs)]

        logger.info(f"Indexando {len(files)} arquivos...")

        for file_path in files:
            try:
                # Ler conteúdo
                content = file_path.read_text(
                    encoding='utf-8', errors='ignore')

                # Dividir em chunks (max 1000 caracteres)
                chunks = [content[i:i + 1000]
                          for i in range(0, len(content), 1000)]

                for idx, chunk in enumerate(chunks):
                    # Gerar embedding
                    embedding = llm.embedding(chunk, model="nomic-embed-text")

                    if embedding:
                        # Metadados
                        metadata = {
                            "source": "codebase",
                            "file": str(file_path.relative_to(base_path)),
                            "language": file_path.suffix[1:],
                            "chunk": idx
                        }

                        # Adicionar ao Qdrant
                        point_id = vs.add_text(chunk, embedding, metadata)

                        if point_id:
                            # Registrar no banco
                            conn = db._get_conn()
                            cursor = conn.cursor()
                            cursor.execute(
                                "INSERT OR REPLACE INTO code_index (file_path, chunk_id, content, language, indexed_at) VALUES (?, ?, ?, ?, ?)",
                                (str(file_path),
                                 f"{file_path.name}_{idx}",
                                    chunk,
                                    file_path.suffix[1:],
                                    time.time())
                            )
                            conn.commit()
                            conn.close()
                            indexed += 1
                        else:
                            skipped += 1
                    else:
                        errors += 1

            except Exception as e:
                logger.error(f"Erro ao indexar {file_path}: {e}")
                errors += 1

        return f"""✅ Indexação Completa:
- Arquivos processados: {len(files)}
- Chunks indexados: {indexed}
- Já existiam: {skipped}
- Erros: {errors}"""

    except Exception as e:
        logger.error(f"Erro na indexação: {e}")
        return f"❌ Erro: {e}"
