"""
Auto Retrainer - Retreinamento automático periódico
Verifica dados novos e retreina adapters quando necessário
"""

import logging
from typing import Dict
from core.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AutoRetrainer")


class AutoRetrainer:
    """
    Sistema de retreinamento automático
    Verifica dados e retreina quando threshold atingido
    """

    def __init__(
        self,
        min_examples: int = 100,
        min_quality: float = 0.8
    ):
        """
        Inicializa retrainer

        Args:
            min_examples: Mínimo de exemplos para retreinar
            min_quality: Score mínimo dos exemplos
        """
        self.db = DatabaseManager()
        self.min_examples = min_examples
        self.min_quality = min_quality

        logger.info("✅ Auto Retrainer inicializado")
        logger.info(f"   Min examples: {min_examples}")
        logger.info(f"   Min quality: {min_quality}")

    def should_retrain(self) -> bool:
        """
        Verifica se deve retreinar

        Returns:
            True se deve retreinar
        """
        try:
            conn = self.db._get_conn()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM training_data
                WHERE quality_score >= ?
            """, (self.min_quality,))

            count = cursor.fetchone()[0]
            conn.close()

            should = count >= self.min_examples

            if should:
                logger.info(
                    f"✅ Deve retreinar: {count} exemplos disponíveis")
            else:
                logger.info(
                    f"ℹ️  Não deve retreinar: {count}/{self.min_examples} exs")

            return should

        except Exception as e:
            logger.error(f"Erro ao verificar: {e}")
            return False

    def get_training_stats(self) -> Dict:
        """
        Retorna estatísticas de dados de treinamento
        """
        try:
            conn = self.db._get_conn()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM training_data")
            total = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM training_data
                WHERE quality_score >= ?
            """, (self.min_quality,))
            high_quality = cursor.fetchone()[0]

            cursor.execute("""
                SELECT task_type, COUNT(*), AVG(quality_score)
                FROM training_data
                WHERE quality_score >= ?
                GROUP BY task_type
            """, (self.min_quality,))

            by_type = {}
            for row in cursor.fetchall():
                by_type[row[0]] = {
                    'count': row[1],
                    'avg_quality': round(row[2], 2)
                }

            conn.close()

            return {
                'total': total,
                'high_quality': high_quality,
                'by_type': by_type,
                'ready_to_train': high_quality >= self.min_examples
            }

        except Exception as e:
            logger.error(f"Erro ao obter stats: {e}")
            return {}

    def retrain(self) -> bool:
        """
        Executa retreinamento
        """
        try:
            logger.info("🔄 Iniciando retreinamento...")

            if not self.should_retrain():
                logger.warning("⚠️  Dados insuficientes para retreinar")
                return False

            logger.info("📊 Preparando dados...")
            stats = self.get_training_stats()
            logger.info(f"   Total: {stats['high_quality']} exemplos")
            logger.info(f"   Por tipo: {stats['by_type']}")

            logger.info("🎯 Retreinamento seria executado aqui")
            logger.info("   (Requer GPU e tempo ~30min)")

            return True

        except Exception as e:
            logger.error(f"Erro ao retreinar: {e}")
            return False


_retrainer = None


def get_retrainer() -> AutoRetrainer:
    """Retorna instância singleton"""
    global _retrainer
    if _retrainer is None:
        _retrainer = AutoRetrainer()
    return _retrainer


if __name__ == "__main__":
    print("🧪 Testando Auto Retrainer...")
    retrainer = AutoRetrainer(min_examples=100)
    print("\n1️⃣ Verificando se deve retreinar...")
    should = retrainer.should_retrain()
    print(f"   Resultado: {should}")
    print("\n2️⃣ Estatísticas de treinamento:")
    stats = retrainer.get_training_stats()
    print(f"   Total: {stats.get('total', 0)}")
    print(f"   Alta qualidade: {stats.get('high_quality', 0)}")
    print(f"   Pronto: {stats.get('ready_to_train', False)}")
    print(f"   Por tipo: {stats.get('by_type', {})}")
    if should:
        print("\n3️⃣ Simulando retreinamento...")
        success = retrainer.retrain()
        print(f"   Sucesso: {success}")
    print("\n✅ Testes concluídos!")