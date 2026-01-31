"""
Knowledge Crawler - Rastreador de conhecimento local
Escaneia diretórios e ingere documentos/código no Vector Database
"""

import os
import logging
import hashlib
from typing import List, Dict, Optional
from pathlib import Path

try:
    from rich.console import Console
    console = Console()
except ImportError:
    console = None

from core.rag_helper import get_rag_helper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KnowledgeCrawler")


class KnowledgeCrawler:
    """
    Rastreador recursivo de arquivos locais para ingestão no RAG
    """

    SUPPORTED_EXTENSIONS = {
        '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
        '.sh': 'shell', '.json': 'json', '.md': 'markdown',
        '.txt': 'text', '.pdf': 'pdf'
    }

    IGNORE_DIRS = {
        'venv', '__pycache__', '.git', 'node_modules',
        'dist', 'build', '.idea', '.vscode', 'logs'
    }

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path).resolve()
        self.rag = get_rag_helper()
        self.stats = {'processed': 0, 'skipped': 0, 'errors': 0}
        logger.info(f"✅ Crawler inicializado em: {self.base_path}")

    def crawl(self, path: Optional[str] = None) -> Dict:
        """
        Inicia o processo de crawling
        """
        start_path = Path(path).resolve() if path else self.base_path
        if not start_path.exists():
            logger.error(f"Caminho não encontrado: {start_path}")
            return self.stats
        logger.info(f"🚀 Iniciando varredura em: {start_path}")
        if console:
            console.print(
                f"[bold cyan]🚀 Varredura em:[/bold cyan] {start_path}")
        files_to_process = []
        for root, dirs, files in os.walk(start_path):
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            for file in files:
                file_path = Path(root) / file
                if self._is_supported(file_path):
                    files_to_process.append(file_path)
        total = len(files_to_process)
        logger.info(f"📁 Arquivos identificados: {total}")
        for idx, file_path in enumerate(files_to_process, 1):
            try:
                self._process_file(file_path)
                self.stats['processed'] += 1
                if idx % 10 == 0:
                    logger.info(f"⏳ Processado {idx}/{total}...")
            except Exception as e:
                logger.error(f"Erro ao processar {file_path}: {e}")
                self.stats['errors'] += 1
        logger.info(f"🏁 Finalizado! Stats: {self.stats}")
        if console:
            console.print(
                f"[bold green]🏁 Finalizado![/bold green] Stats: {self.stats}")
        return self.stats

    def _is_supported(self, path: Path) -> bool:
        return path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def _process_file(self, path: Path):
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
            if not content.strip():
                self.stats['skipped'] += 1
                return
            rel_path = path.relative_to(self.base_path)
            file_type = self.SUPPORTED_EXTENSIONS[path.suffix.lower()]
            meta = {
                "source": str(rel_path),
                "type": file_type,
                "timestamp": os.path.getmtime(path)
            }
            chunks = self._chunk_content(content)
            for i, chunk in enumerate(chunks):
                embedding = self.rag.get_embedding(chunk)
                if not embedding:
                    logger.warning(
                        f"Falha ao gerar embedding para chunk de {path}")
                    continue
                self.rag.vector_store.add_texts(
                    texts=[chunk],
                    embeddings=[embedding],
                    metadatas=[meta]
                )
        except Exception as e:
            raise e

    def _chunk_content(self, content: str, chunk_size: int = 1000,
                       overlap: int = 100) -> List[str]:
        if len(content) <= chunk_size:
            return [content]
        chunks = []
        start = 0
        while start < len(content):
            end = start + chunk_size
            chunk = content[start:end]
            chunks.append(chunk)
            start += (chunk_size - overlap)
        return chunks


_crawler = None


def get_knowledge_crawler() -> KnowledgeCrawler:
    global _crawler
    if _crawler is None:
        _crawler = KnowledgeCrawler(os.getcwd())
    return _crawler


if __name__ == "__main__":
    print("🕷️ Testando Knowledge Crawler...")
    crawler = KnowledgeCrawler()
    stats = crawler.crawl("scripts")
    print(f"Resultado: {stats}")