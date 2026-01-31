import logging
import time
from core.rag_helper import RAGHelper
from core.p2p_learning import GabrielleConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LatentBenchmark")


def run_benchmark():
    rag = RAGHelper()
    conn = GabrielleConnector(host="100.114.201.84", port=9000)

    if not conn.is_connected:
        print("❌ Gabrielle offline. Verifique a conexão.")
        return

    query = "Quais as capacidades de visão da Ziva?"
    print(f"🔍 Query: {query}")

    # 1. Benchmark: Latent RAG
    print("\n--- ⚡ Testando Latent RAG ---")
    start_latent = time.time()

    # Gerar embedding localmente
    embedding = rag.get_embedding(query)
    if not embedding:
        print("❌ Falha ao gerar embedding local")
        return

    # Buscar remotamente via Latent Channel
    context_latent = conn.search_remote_latent(embedding)
    latent_time = time.time() - start_latent

    print(f"⏱️ Tempo Latent RAG: {latent_time:.3f}s")
    print(f"📄 Contexto ({len(context_latent)} chars):")
    print(f"{context_latent[:200]}...")

    # 2. Benchmark: Text RPC (Simulado via ask_remote_llm que agora usa
    # msgpack)
    print("\n--- 📝 Testando Text RPC (Legacy) ---")
    start_text = time.time()
    # No RPC tradicional, o worker teria que re-gerar o embedding
    resp_text = conn.ask_remote_llm(
        f"Baseado no seu conhecimento local, {query}")
    text_time = time.time() - start_text

    print(f"⏱️ Tempo Text RPC: {text_time:.3f}s")

    print("\n📊 Resumo:")
    print(f"Latent RAG: {latent_time:.3f}s")
    print(f"Text RPC:   {text_time:.3f}s (Inference)")

    if latent_time < text_time:
        print(f"🚀 Latent RAG é {(text_time /
                                 latent_time):.1f}x mais rápido para recuperação de contexto!")


if __name__ == "__main__":
    run_benchmark()
