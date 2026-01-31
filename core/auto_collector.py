import logging
from typing import Dict
from core.database import DatabaseManager
from core.confidence_scorer import get_confidence_scorer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AutoCollector")


class AutoCollector:
    """
    Coleta automaticamente exemplos de alta qualidade para retreinamento
    Com validação de confiabilidade 0.9-1.0
    """

    def __init__(self, min_quality: float = 0.9):
        """
        Inicializa collector

        Args:
            min_quality: Score mínimo para salvar (0.9-1.0)
        """
        self.db = DatabaseManager()
        self.scorer = get_confidence_scorer()
        self.min_quality = min_quality

        logger.info(
            f"✅ Auto Collector inicializado (min_quality: {min_quality})")

    def process_interaction(
        self,
        query: str,
        response: str,
        task_type: str = 'general'
    ) -> bool:
        """
        Processa interação com validação de alta confiabilidade

        Args:
            query: Pergunta do usuário
            response: Resposta gerada
            task_type: Tipo de tarefa

        Returns:
            True se salvou, False caso contrário
        """
        try:
            # Importar improver
            from core.response_improver import get_response_improver
            improver = get_response_improver()

            # Avaliar confiança inicial
            score = self.scorer.score(query, response)

            logger.info(f"📊 Score inicial: {score:.2f}")

            # Se baixo, tentar melhorar
            if score < self.min_quality:
                logger.info(
                    f"⚠️  Score < {
                        self.min_quality}, tentando melhorar...")

                improved_response, new_score = improver.improve(
                    query,
                    response,
                    max_iterations=3
                )

                if new_score >= self.min_quality:
                    logger.info(f"✅ Melhorado! {score:.2f} → {new_score:.2f}")
                    response = improved_response
                    score = new_score
                else:
                    logger.warning(
                        f"⚠️  Não atingiu threshold: {
                            new_score:.2f}")
                    return False

            # Salvar se alta qualidade
            if score >= self.min_quality:
                self.db.add_training_data(
                    instruction=query,
                    output=response,
                    task_type=task_type,
                    quality_score=score
                )

                logger.info(
                    f"💾 Exemplo salvo (score: {
                        score:.2f}, type: {task_type})")
                return True

            return False

        except Exception as e:
            logger.error(f"Erro ao processar interação: {e}")
            return False

    def get_stats(self) -> Dict:
        """
        Retorna estatísticas de coleta

        Returns:
            Dict com estatísticas
        """
        try:
            conn = self.db._get_conn()
            cursor = conn.cursor()

            # Total
            cursor.execute("SELECT COUNT(*) FROM training_data")
            total = cursor.fetchone()[0]

            # Alta qualidade
            cursor.execute(
                "SELECT COUNT(*) FROM training_data WHERE quality_score >= ?",
                (self.min_quality,)
            )
            high_quality = cursor.fetchone()[0]

            # Por tipo
            cursor.execute(
                "SELECT task_type, COUNT(*) FROM training_data "
                "WHERE quality_score >= ? GROUP BY task_type",
                (self.min_quality,)
            )
            by_type = dict(cursor.fetchall())

            conn.close()

            return {
                'total': total,
                'high_quality': high_quality,
                'by_type': by_type,
                'min_quality': self.min_quality
            }

        except Exception as e:
            logger.error(f"Erro ao obter stats: {e}")
            return {}


# Singleton
_collector = None


def get_collector() -> AutoCollector:
    """Retorna instância singleton"""
    global _collector
    if _collector is None:
        _collector = AutoCollector()
    return _collector


# Teste
if __name__ == "__main__":
    print("🧪 Testando Auto Collector...")

    collector = AutoCollector(min_quality=0.7)

    # Teste 1: Exemplo de alta qualidade
    print("\n1️⃣ Teste: Exemplo de alta qualidade")
    saved = collector.process_interaction(
        query="Como usar async/await em JavaScript?",
        response="Async/await é uma sintaxe moderna para trabalhar com Promises...",
        task_type="coding")
    print(f"   Salvou: {saved}")

    # Teste 2: Exemplo de baixa qualidade
    print("\n2️⃣ Teste: Exemplo de baixa qualidade")
    saved = collector.process_interaction(
        query="oi",
        response="olá",
        task_type="general"
    )
    print(f"   Salvou: {saved}")

    # Teste 3: Estatísticas
    print("\n3️⃣ Estatísticas:")
    stats = collector.get_stats()
    print(f"   Total: {stats.get('total', 0)}")
    print(f"   Alta qualidade: {stats.get('high_quality', 0)}")
    print(f"   Por tipo: {stats.get('by_type', {})}")

    print("\n✅ Testes concluídos!")
