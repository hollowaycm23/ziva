from core.llm import LLMService
from core.vector_store import VectorStore
import sys
import os
import logging
from pathlib import Path

# Setup path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SessionIngestor")


def ingest_session_history():
    brain_dir = Path(
        "/home/holloway/.gemini/antigravity/brain/c68c5448-bf92-4355-b969-a78fbc4b7a8a")
    if not brain_dir.exists():
        logger.error("Diretório brain não encontrado.")
        return

    vs = VectorStore()
    llm = LLMService(model="nomic-embed-text")

    # Lista arquivos .md (artifacts)
    md_files = list(brain_dir.glob("*.md"))

    logger.info(
        f"Iniciando ingestão de {
            len(md_files)} artefatos de sessão...")

    for md_file in md_files:
        logger.info(f"Processando {md_file.name}...")
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Divide em parágrafos ou seções para melhor granularidade no RAG
        sections = content.split("\n\n")
        for i, section in enumerate(sections):
            if len(section.strip()) < 100:
                continue

            text = f"[SESSÃO ANTIGRAVITY - {md_file.stem}] {section}"
            embedding = llm.embedding(text)
            if embedding:
                vs.add_text(text, embedding, {
                    "source": f"antigravity_session_{md_file.stem}",
                    "type": "process_memory"
                })

    logger.info("Ingestão de histórico de sessão Antigravity concluída.")


if __name__ == "__main__":
    ingest_session_history()
