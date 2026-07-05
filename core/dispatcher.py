import logging
import json
from core.database import DatabaseManager
from core.registry import NodeRegistry

logger = logging.getLogger("JobDispatcher")


class JobDispatcher:
    """
    Responsável por analisar jobs pendentes e decidir o nó de execução.
    """

    def __init__(self):
        self.db = DatabaseManager()
        self.registry = NodeRegistry()
        self.local_node_id = "node07"

    def dispatch_pending_jobs(self):
        job = self.db.get_pending_job()
        if not job:
            return

        target_node = self._decide_target(job)
        self.db.update_job_status(job['id'], 'assigned')
        self._set_assigned_node(job['id'], target_node)

        if target_node == self.local_node_id:
            logger.info(f"Job {job['id']} atribuído localmente (Ziva).")
        else:
            logger.info(f"Job {job['id']} atribuído a {target_node}.")
            self._send_to_remote(job, target_node)

    def _decide_target(self, job):
        payload = job.get('payload', {})
        if payload.get('requirements') == 'heavy_computation':
            workers = self.registry.list_workers()
            if workers:
                return workers[0]['id']
        return self.local_node_id

    def _set_assigned_node(self, job_id, node_id):
        conn = self.db._get_conn()
        conn.execute(
            "UPDATE jobs SET assigned_node = ? WHERE id = ?",
            (node_id, job_id))
        conn.commit()
        conn.close()

    def _send_to_remote(self, job, node_id):
        import time
        import os
        filename = f"job_{job['id']}_{int(time.time())}.json"
        outbox_dir = os.getenv("ZIVA_OUTBOX_DIR", "/app/outbox")
        filepath = f"{outbox_dir}/{filename}"

        task_packet = {
            "type": "job_execution",
            "job_id": job['id'],
            "origin": self.local_node_id,
            "payload": job['payload']
        }

        with open(filepath, 'w') as f:
            json.dump(task_packet, f)

        logger.info(f"Pacote de tarefa criado em {filepath} para {node_id}")

    def get_next_job(self):
        """Wrapper para buscar próximo job atribuído localmente."""
        self.dispatch_pending_jobs()
        return self.db.get_next_local_job(self.local_node_id)

    def complete_job(self, job_id, result):
        """Wrapper para completar job."""
        self.db.update_job_status(job_id, 'completed', result)