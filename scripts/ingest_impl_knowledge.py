from core.llm import LLMService
from core.vector_store import VectorStore
import sys
import os
import logging
from pathlib import Path

# Setup path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Ingestor")


def ingest_implementation_knowledge():
    # Caminhos
    brain_dir = Path(
        "/home/holloway/.gemini/antigravity/brain/c68c5448-bf92-4355-b969-a78fbc4b7a8a")
    implementation_plan = brain_dir / "implementation_plan.md"
    task_md = brain_dir / "task.md"
    walkthrough = brain_dir / "walkthrough.md"

    # For now, we'll use implementation_plan as the primary digest
    digest_path = implementation_plan

    if not digest_path.exists():
        logger.error(
            f"Digest de implementação não encontrado em {digest_path}.")
        return

    # Inicializa serviços
    vs = VectorStore()
    # PULL nomic-embed-text if needed or ensure it is used
    llm = LLMService(model="nomic-embed-text")

    with open(digest_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by headers to create smaller, meaningful chunks
    chunks = content.split("##")

    logger.info(
        f"Iniciando ingestão de {
            len(chunks)} tópicos de implementação...")

    for i, chunk in enumerate(chunks):
        if len(chunk.strip()) < 50:
            continue

        text = "##" + chunk
        logger.info(f"Vetorizando tópico {i + 1}...")

        embedding = llm.embedding(text)
        if embedding:
            vs.add_text(text, embedding, {
                "source": "implementation_process",
                "topic_index": i,
                "type": "technical_doc"
            })

    logger.info(
        "Ingestão concluída. Ziva agora conhece sua própria estrutura atualizada.")


if __name__ == "__main__":
    ingest_implementation_knowledge()
