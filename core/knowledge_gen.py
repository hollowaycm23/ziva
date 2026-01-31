import logging
from core.database import DatabaseManager
from core.vector_store import VectorStore
from core.vector_store import VectorStore
from core.llm import LLMService
from core.config import config

logger = logging.getLogger("KnowledgeGenerator")


class KnowledgeGenerator:
    """
    Consolidador de Memória de Sessão.
    """

    def __init__(self, knowledge_client=None, llm_client=None):
        self.db = DatabaseManager()
        self.knowledge = knowledge_client or VectorStore()
        self.llm = llm_client or LLMService()
        self.chat_model = "qwen2.5-coder:7b"
        self.chat_model = "qwen2.5-coder:7b"
        emb_config = config.get_llm_provider("agent.embedding_model")
        self.embed_model = emb_config["model_name"] if emb_config else "text-embedding-qwen2.5-0.5b-instruct"

    def process_completed_sessions(self):
        """Busca sessões completadas mas não processadas para aprendizado."""
        conn = self.db._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE status = 'completed'")
        sessions = cursor.fetchall()

        for sess in sessions:
            sess_id = sess[0]
            logger.info(f"Processando aprendizado da sessão {sess_id}...")
            cursor.execute(
                "SELECT role, content FROM interactions WHERE session_id = ? "
                "ORDER BY timestamp ASC", (sess_id,))
            interactions = cursor.fetchall()
            chat_history = "\n".join([f"{r}: {c}" for r, c in interactions])
            doc = self._generate_technical_doc(chat_history)
            if doc:
                embedding = self.llm.embedding(doc, model=self.embed_model)
                if embedding:
                    self.knowledge.add_text(doc, embedding, {
                        "source": f"session_{sess_id}",
                        "type": "learning_doc"
                    })
                    logger.info(
                        f"Documentação da sessão {sess_id} memorizada.")
            cursor.execute(
                "UPDATE sessions SET status = 'learned', summary = ? "
                "WHERE id = ?", (doc, sess_id))
            conn.commit()
        conn.close()

    def _generate_technical_doc(self, chat_history):
        """Usa o LLM para destilar a conversa em conhecimento útil."""
        prompt = f"""
        [CONSOLIDADOR DE CONHECIMENTO ZIVA]
        Analise o histórico de conversa abaixo e gere uma DOCUMENTAÇÃO TÉCNICA
        contendo os principais tópicos discutidos, decisões tomadas,
        comandos executados e lições aprendidas.

        HISTÓRICO:
        {chat_history[:4000]}

        RESPONDA EM MARKDOWN TÉCNICO E CONCISO.
        """
        return self.llm.completion(
            prompt, temperature=0.2, model=self.chat_model)