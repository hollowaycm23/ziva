import logging
from core.rag_helper import RAGHelper

logging.basicConfig(level=logging.INFO)


def test_rag_compression():
    rag = RAGHelper()

    query = "O que é Ziva Advanced Architectures?"

    # Simular contexto longo
    long_context = """
    Ziva Advanced Architectures v2.3 Polymath é um sistema cognitivo avançado que foca em memória contextual.
    O sistema utiliza Qdrant para armazenamento vetorial e suporta múltiplos modelos como DeepSeek e Llama.
    A arquitetura v2.3 introduziu o crawler de conhecimento e o sistema de curiosidade ativa.
    Ziva é capaz de realizar fine-tuning local usando QLoRA na RTX 4070.
    O protocolo HEX-COM é usado para comunicação entre agentes internos.
    O sistema possui uma interface web moderna baseada em Glassmorphism.
    Ziva foca em eficiência de tokens e agora suporta protocolos binários como Msgpack.
    """

    print(f"--- Original Context ({len(long_context)} chars) ---")
    print(long_context)

    print("\n--- Compressing Context... ---")
    compressed = rag.compress_context(long_context, query)

    print(f"\n--- Compressed Context ({len(compressed)} chars) ---")
    print(compressed)

    reduction = (1 - len(compressed) / len(long_context)) * 100
    print(f"\n📊 Redução: {reduction:.1f}%")


if __name__ == "__main__":
    test_rag_compression()
