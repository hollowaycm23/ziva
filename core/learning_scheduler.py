"""
Automated Learning Scheduler for Ziva.
"""

import logging
import time
import threading
from typing import Optional
from core.training_data_collector import TrainingDataCollector
from core.learning import SelfLearner
from core.database import DatabaseManager

logger = logging.getLogger("LearningScheduler")


class LearningScheduler:
    """
    Agendador automático para ciclos de aprendizado.
    """

    def __init__(self,
                 collection_interval: int = 21600,
                 training_threshold: int = 50,
                 min_quality: float = 0.8):
        """
        Inicializa o scheduler.
        """
        self.collection_interval = collection_interval
        self.training_threshold = training_threshold
        self.min_quality = min_quality

        self.collector = TrainingDataCollector()
        self.learner = SelfLearner()
        self.db = DatabaseManager()

        self.running = False
        self.thread: Optional[threading.Thread] = None

        self.last_collection_time = 0
        self.last_training_time = 0
        self.total_collected = 0
        self.total_trained = 0

    def start(self):
        """Inicia o scheduler em background thread"""
        if self.running:
            logger.warning("Scheduler já está rodando")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info(
            f"🎓 Learning Scheduler iniciado (intervalo: {self.collection_interval}s)")

    def stop(self):
        """Para o scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("🛑 Learning Scheduler parado")

    def _run_loop(self):
        """Loop principal do scheduler"""
        while self.running:
            try:
                current_time = time.time()
                if current_time - self.last_collection_time >= self.collection_interval:
                    self._collect_training_data()
                    self.last_collection_time = current_time
                new_examples = self._count_new_examples()
                if new_examples >= self.training_threshold:
                    self._trigger_training()
                time.sleep(60)
            except Exception as e:
                logger.error(f"Erro no loop do scheduler: {e}")
                time.sleep(300)

    def _collect_training_data(self):
        """Coleta dados de treinamento das sessões recentes"""
        try:
            logger.info("📚 Iniciando coleta de dados de treinamento...")
            collected = self.collector.collect_from_sessions(
                min_quality=self.min_quality)
            insights = self.learner.run_cycle()
            self.total_collected += collected
            logger.info(
                f"✅ Coleta completa: {collected} exs, {len(insights)} insights")
            self._log_metric("data_collection", {
                "examples_collected": collected,
                "insights_generated": len(insights),
                "timestamp": time.time()
            })
        except Exception as e:
            logger.error(f"Erro na coleta de dados: {e}")

    def _count_new_examples(self) -> int:
        """Conta exemplos não usados em treinamento"""
        conn = self.db._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM training_data
            WHERE used_in_training = 0 AND quality_score >= ?
        ''', (self.min_quality,))
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def _trigger_training(self):
        """Triggera treinamento LoRA"""
        try:
            logger.info("🏋️ Triggerando treinamento LoRA...")
            dataset = self.collector.get_diverse_dataset(
                target_size=100,
                min_quality=self.min_quality
            )
            if len(dataset) < 20:
                logger.warning(
                    f"Dataset muito pequeno ({len(dataset)}), pulando.")
                return
            dataset_path = f"/home/holloway/ziva/data/training/auto_training_{int(time.time())}.json"
            self.collector.export_to_json(dataset)
            logger.info(f"✅ Dataset exportado: {dataset_path}")
            logger.debug("Treinamento LoRA agendado")
            self._mark_examples_as_used(dataset)
            self.last_training_time = time.time()
            self.total_trained += len(dataset)
            self._log_metric("training_triggered", {
                "dataset_size": len(dataset),
                "dataset_path": dataset_path,
                "timestamp": time.time()
            })
        except Exception as e:
            logger.error(f"Erro ao triggerar treinamento: {e}")

    def _mark_examples_as_used(self, dataset):
        """Marca exemplos como usados em treinamento"""
        conn = self.db._get_conn()
        cursor = conn.cursor()
        for example in dataset:
            cursor.execute('''
                UPDATE training_data
                SET used_in_training = 1
                WHERE instruction = ? AND output = ?
            ''', (example['instruction'], example['output']))
        conn.commit()
        conn.close()

    def _log_metric(self, metric_type: str, data: dict):
        """Registra métrica de aprendizado"""
        conn = self.db._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_type TEXT NOT NULL,
                data TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        ''')
        import json
        cursor.execute('''
            INSERT INTO learning_metrics (metric_type, data, timestamp)
            VALUES (?, ?, ?)
        ''', (metric_type, json.dumps(data), time.time()))
        conn.commit()
        conn.close()

    def get_stats(self) -> dict:
        """Retorna estatísticas do scheduler"""
        return {
            "running": self.running,
            "total_collected": self.total_collected,
            "total_trained": self.total_trained,
            "last_collection": self.last_collection_time,
            "last_training": self.last_training_time,
            "new_examples_available": self._count_new_examples()
        }


_scheduler_instance: Optional[LearningScheduler] = None


def get_scheduler() -> LearningScheduler:
    """Retorna instância singleton do scheduler"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = LearningScheduler()
    return _scheduler_instance


if __name__ == "__main__":
    scheduler = LearningScheduler(collection_interval=60)
    scheduler.start()
    try:
        while True:
            time.sleep(30)
            stats = scheduler.get_stats()
            print(f"📊 Stats: {stats}")
    except KeyboardInterrupt:
        scheduler.stop()