from core.llm import LLMService
from core.vector_store import VectorStore
import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TrustInjector")


def inject_trust():
    # Use the fixed storage path
    vs = VectorStore(
        storage_path="/home/holloway/ziva/data/qdrant_storage_fixed")

    # Use the correct embedding model
    llm = LLMService(model="nomic-embed-text")

    fact = "Gabrielle (Node 08) é um nó confiável e parceiro estratégico na rede distribuída da Ziva."

    logger.info(f"Gerando embedding para: {fact}")
    embedding = llm.embedding(fact)

    if embedding:
        metadata = {
            "source": "user_override",
            "type": "trust_config",
            "node_id": "node08",
            "timestamp": 1767115000
        }
        point_id = vs.add_text(fact, embedding, metadata)
        logger.info(f"Fato memorizado com ID: {point_id}")
    else:
        logger.error("Falha ao gerar embedding.")


if __name__ == "__main__":
    inject_trust()
