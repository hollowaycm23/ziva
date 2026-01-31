"""
RAG Helper - Retrieval-Augmented Generation
Integra busca semântica no Qdrant com geração de respostas
"""

import logging
import requests
from typing import List, Dict, Optional
from core.vector_stores.factory import get_vector_store
from core.reranker import get_reranker
from sentence_transformers import SentenceTransformer


logger = logging.getLogger("RAGHelper")

# Reranking configuration
RERANK_OVERSAMPLING_FACTOR = 4  # Retrieve 4x candidates for reranking


class RAGHelper:
    """
    Helper para Retrieval-Augmented Generation
    Busca contexto relevante no Qdrant antes de gerar respostas
    """

    def __init__(self, ollama_url: str = "http://127.0.0.1:11434"):
        """
        Inicializa RAG Helper
        """
        self.vector_store = get_vector_store()
        self.ollama_url = ollama_url
        self._encoder = None  # Lazy-loaded via property
        logger.info("✅ RAG Helper inicializado (Multilingual - Lazy Load)")

    def get_embedding(self, text: str) -> List[float]:
        """
        Gera embedding usando LLMservice (consistente com resto do sistema - 768d)
        """
        try:
            from core.llm import LLMService
            llm = LLMService()
            # Precisamos usar o mesmo modelo que criou a collection (provavelmente nomic ou ziva-base)
            # Assumindo nomic-embed-text que geralmente e 768
            return llm.embedding(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []

    def search_memories(
        self,
        query: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        limit: int = 3,
        min_score: float = 0.5
    ) -> List[Dict]:
        """
        Busca memórias relevantes no Qdrant.
        Suporta busca por texto (query) ou diretamente por vetor (embedding).
        """
        try:
            # Se não temos embedding, geramos da query
            if embedding is None:
                if query is None:
                    return []
                embedding = self.get_embedding(query)

            if not embedding:
                logger.warning("Embedding vazio ou falha na geração")
                return []

            # Buscar no armazenamento vetorial
            # Retrieve more candidates for reranking
            candidates_limit = limit * RERANK_OVERSAMPLING_FACTOR
            results = self.vector_store.search(
                embedding, 
                limit=candidates_limit,
                query_text=query # Ativa busca híbrida se suportado pelo backend
            )

            # --- Active Recall Logic (Sprint 28) ---
            # Boost score para lições aprendidas
            for res in results:
                meta = res.get('metadata', {})
                if meta.get('type') == 'learned_lesson' or meta.get(
                        'source') == 'thought_police':
                    # Boost de 25% na relevância
                    res['score'] = res.get('score', 0) * 1.25
                    logger.info(f"🚀 Active Recall triggered for: {res.get('text')[:30]}... (New Score: {res['score']:.2f})")

            # --- Semantic Reranking (Cross-Encoder) ---
            # Re-order based on true relevance to the query
            reranker = get_reranker()
            if query:
                logger.info(f"⚖️ Reranking {len(results)} candidates for query: '{query}'")
                results = reranker.rerank(query, results, top_k=limit)
            else:
                # If no textual query (embedding only search), fallback to
                # vector score
                results.sort(key=lambda x: x.get('score', 0), reverse=True)
                results = results[:limit]
            # ---------------------------------------

            # Filtrar por score
            filtered = [r for r in results if r.get('score', 0) >= min_score]

            logger.info(f"🔍 Encontradas {len(filtered)} memórias relevantes")
            return filtered

        except Exception as e:
            logger.error(f"Erro ao buscar memórias: {e}")
            return []

    def format_context(
            self, memories: List[Dict], max_length: int = 500) -> str:
        """
        Formata memórias em contexto para o prompt
        """
        if not memories:
            return ""

        context_parts = []
        for i, mem in enumerate(memories, 1):
            text = mem.get('text', '')
            score = mem.get('score', 0)

            # Truncar se muito longo
            if len(text) > max_length:
                text = text[:max_length] + "..."

            context_parts.append(
                f"[Ref: {score:.2f}] {text}"
            )

        return "\n\n".join(context_parts)

    def compress_context(self, context: str, user_query: str) -> str:
        """
        Comprime o contexto para o essencial baseado na query.
        (Fase 1.2 do Sprint 42 - Latent & Binary Optimization)
        """
        if not context or len(context) < 300:  # Não comprime se for pequeno
            return context

        prompt = f"""
        Como um otimizador de densidade de informação, comprima o seguinte contexto para o ESSENCIAL absoluto necessário para responder à pergunta abaixo.

        REGRAS:
        1. Remova redundâncias, introduções e pontuações desnecessárias.
        2. Mantenha fatos técnicos, dados e referências cruciais.
        3. Formato de saída: Texto condensado de alta densidade.
        4. Alvo: Redução de 50% nos tokens sem perder informação semântica.

        PERGUNTA: {user_query}
        CONTEXTO: {context}

        COMPRESSÃO:
        """

        try:
            from core.llm import LLMService
            llm = LLMService()
            compressed = llm.completion(
                prompt, temperature=0.1, max_tokens=256)
            if compressed and len(compressed) < len(context):
                logger.info(
                    f"⚡ Contexto comprimido: {len(context)} -> {len(compressed)} chars")
                return compressed
            return context
        except Exception as e:
            logger.error(f"Erro na compressão de contexto: {e}")
            return context

    def enhance_prompt(
        self,
        user_query: str,
        limit: int = 3,
        min_score: float = 0.4
    ) -> tuple[str, int]:
        """
        Melhora prompt com contexto do Qdrant

        Args:
            user_query: Pergunta do usuário
            limit: Número de memórias para buscar
            min_score: Score mínimo

        Returns:
            (prompt_melhorado, num_memorias_usadas)
        """
        # Buscar memórias relevantes
        memories = self.search_memories(user_query, limit, min_score)

        if not memories:
            # Sem contexto relevante, retorna query original
            return user_query, 0

        # Formatar contexto
        context = self.format_context(memories)

        # Otimização Sprint 42: Compressão de Contexto
        context = self.compress_context(context, user_query)

        # Construir prompt melhorado
        enhanced = f"""Contexto relevante da base de conhecimento:

{context}

---

Pergunta do usuário: {user_query}

Responda usando o contexto acima quando relevante. Se o contexto não for útil, responda normalmente."""

        return enhanced, len(memories)

    def get_all_documents(self, batch_size: int = 100):
        """
        Generator que retorna batches de todos os documentos do Vector Store atual.
        """
        offset = None
        while True:
            try:
                docs, next_offset = self.vector_store.scroll(limit=batch_size, offset=offset)
                
                if not docs:
                    break
                    
                yield docs
                
                if next_offset is None:
                    break
                    
                offset = next_offset
                
            except Exception as e:
                logger.error(f"Erro ao iterar collection: {e}")
                break



# Singleton global
_rag_helper = None


def get_rag_helper() -> RAGHelper:
    """Retorna instância singleton do RAG Helper"""
    global _rag_helper
    if _rag_helper is None:
        _rag_helper = RAGHelper()
    return _rag_helper


# Teste
if __name__ == "__main__":
    print("🧪 Testando RAG Helper...")

    try:
        rag = RAGHelper()

        # Teste 1: Buscar memórias
        print("\n1️⃣ Buscando memórias sobre 'JavaScript'...")
        memories = rag.search_memories(
            "Como usar async/await em JavaScript?", limit=2)
        print(f"   Encontradas: {len(memories)}")

        # Teste 2: Formatar contexto
        if memories:
            print("\n2️⃣ Formatando contexto...")
            context = rag.format_context(memories)
            print(f"   Contexto ({len(context)} chars):")
            print(f"   {context[:200]}...")

        # Teste 3: Enhance prompt
        print("\n3️⃣ Melhorando prompt...")
        enhanced, count = rag.enhance_prompt("O que é TypeScript?", limit=2)
        print(f"   Memórias usadas: {count}")
        print(f"   Prompt ({len(enhanced)} chars)")

        print("\n✅ Testes concluídos!")

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("💡 Certifique-se que Qdrant e Ollama estão rodando")