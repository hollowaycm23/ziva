import logging
import time
from core.database import DatabaseManager
from core.llm import LLMService
from core.vector_store import VectorStore
from core.config import config

logger = logging.getLogger("SelfLearner")


class SelfLearner:
    """
    Sistema de Auto-Aprendizado (Self-Correction/Learning).
    """

    def __init__(self, knowledge_client=None, llm_client=None):
        self.db = DatabaseManager()
        self.knowledge = knowledge_client or VectorStore()
        self.llm = llm_client or LLMService()
        self.chat_model = "qwen2.5-coder:7b"
        
        emb_config = config.get_llm_provider("agent.embedding_model")
        self.embed_model = emb_config["model_name"] if emb_config else "text-embedding-qwen2.5-0.5b-instruct"

    def run_cycle(self):
        """
        Executa um ciclo de aprendizado.
        """
        logger.info("Iniciando ciclo de auto-aprendizado...")
        jobs = self._get_recent_completed_jobs(limit=5)
        new_insights = []
        for job in jobs:
            try:
                insight_text = self._analyze_job(job)
                if insight_text:
                    valid = self._absorb_knowledge(insight_text, job['id'])
                    if valid:
                        new_insights.append({
                            "type": "knowledge_sync",
                            "content": insight_text,
                            "origin_node": "node07",
                            "origin_job": job['id'],
                            "timestamp": time.time()
                        })
            except Exception as e:
                logger.error(f"Erro ao analisar job {job['id']}: {e}")
        return new_insights

    def _get_recent_completed_jobs(self, limit=5):
        conn = self.db._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM jobs WHERE status='completed' "
            "ORDER BY updated_at DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [self.db._row_to_job(r) for r in rows]

    def _analyze_job(self, job):
        """
        Usa o LLM para criticar e extrair lições do job.
        """
        payload = job.get('payload', {})
        result = job.get('result', {})
        prompt = f"""
        [SISTEMA DE AUTO-ANÁLISE]
        Analise a tarefa abaixo e extraia um conhecimento técnico útil.
        Se foi um erro, explique como evitar.

        Tarefa: {payload.get('input', 'Sem input')}
        Resultado: {str(result)[:500]}...

        Gere APENAS o insight/conhecimento de forma concisa.
        Insight:
        """
        response = self.llm.completion(
            prompt, temperature=0.2, model=self.chat_model)
        if response and len(response) > 10:
            return response.strip()
        return None

    def _absorb_knowledge(self, insight, job_id):
        """
        Vetoriza e armazena o insight no Qdrant.
        """
        embedding = self.llm.embedding(insight, model=self.embed_model)
        if not embedding:
            return False
        metadata = {
            "source": "self_learning",
            "origin_job": job_id,
            "type": "insight"
        }
        pid = self.knowledge.add_text(insight, embedding, metadata)
        if pid:
            logger.info(f"Insight aprendido: {insight[:50]}...")
            return True
        else:
            logger.debug("Insight já conhecido.")
            return False