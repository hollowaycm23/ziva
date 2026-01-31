#!/usr/bin/env python3
"""
Auto-Retrain Pipeline
Pipeline automático de retreinamento baseado em dados coletados
"""

from core.database import DatabaseManager
from core.quality_scorer import QualityScorer
from core.session_logger import SessionLogger
import sys
import time
import logging
from pathlib import Path

sys.path.insert(0, '/home/holloway/ziva')


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AutoRetrain")


class AutoRetrainPipeline:
    """Pipeline automático de retreinamento"""

    def __init__(
        self,
        min_new_examples: int = 100,
        min_quality_score: float = 0.8,
        auto_trigger: bool = False
    ):
        self.session_logger = SessionLogger()
        self.quality_scorer = QualityScorer()
        self.db_manager = DatabaseManager()

        self.min_new_examples = min_new_examples
        self.min_quality_score = min_quality_score
        self.auto_trigger = auto_trigger

    def check_retrain_conditions(self) -> bool:
        """Verifica se deve retreinar"""
        stats = self.session_logger.get_statistics()

        ready_count = stats['ready_for_training']

        logger.info(f"📊 Dados prontos para treinamento: {ready_count}")

        if ready_count >= self.min_new_examples:
            logger.info(
                f"✅ Condições atendidas! ({ready_count} >= {
                    self.min_new_examples})")
            return True
        else:
            logger.info(
                f"⏳ Aguardando mais dados ({ready_count}/{self.min_new_examples})")
            return False

    def score_unscored_interactions(self):
        """Avalia interações que ainda não têm score"""
        logger.info("🔍 Buscando interações não avaliadas...")

        interactions = self.session_logger.get_unscored_interactions(
            limit=1000)

        if not interactions:
            logger.info("✓ Todas as interações já foram avaliadas")
            return

        logger.info(f"📝 Avaliando {len(interactions)} interações...")

        scores = self.quality_scorer.batch_score(interactions)

        # Atualizar scores no banco
        for interaction_id, score in scores:
            self.session_logger.update_quality_score(interaction_id, score)

        # Estatísticas
        high_quality = sum(
            1 for _, score in scores if score >= self.min_quality_score)
        logger.info(
            f"✅ {high_quality}/{len(interactions)} interações de alta qualidade")

    def prepare_training_data(self) -> int:
        """Prepara dados para treinamento"""
        logger.info("📦 Preparando dados de treinamento...")

        # Buscar interações de alta qualidade
        interactions = self.session_logger.get_high_quality_interactions(
            min_score=self.min_quality_score,
            limit=1000
        )

        if not interactions:
            logger.warning("⚠️ Nenhuma interação de alta qualidade encontrada")
            return 0

        logger.info(f"✓ {len(interactions)} interações selecionadas")

        # Inserir no banco de treinamento
        inserted = 0
        for interaction in interactions:
            try:
                self.db_manager.insert_training_data(
                    instruction=interaction['instruction'],
                    output=interaction['output'],
                    task_type='session_collected',
                    quality_score=self.min_quality_score
                )
                inserted += 1
            except Exception as e:
                logger.debug(f"Interação já existe ou erro: {e}")

        logger.info(
            f"✅ {inserted} novos exemplos adicionados ao dataset de treinamento")

        return inserted

    def trigger_training(self):
        """Dispara processo de treinamento"""
        logger.info("🏋️ Iniciando treinamento...")

        import subprocess

        try:
            result = subprocess.run(
                ["/usr/bin/python3", "/home/holloway/ziva/training/lora_trainer.py"],
                capture_output=True,
                text=True,
                timeout=3600  # 1 hora timeout
            )

            if result.returncode == 0:
                logger.info("✅ Treinamento concluído com sucesso!")
                return True
            else:
                logger.error(f"❌ Treinamento falhou: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("❌ Treinamento excedeu timeout de 1 hora")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar treinamento: {e}")
            return False

    def run_pipeline(self):
        """Executa pipeline completo"""
        logger.info("🚀 Iniciando Auto-Retrain Pipeline")
        logger.info("=" * 60)

        # Passo 1: Avaliar interações não pontuadas
        logger.info("\n📋 Passo 1: Avaliação de Qualidade")
        self.score_unscored_interactions()

        # Passo 2: Verificar se deve retreinar
        logger.info("\n📋 Passo 2: Verificação de Condições")
        should_retrain = self.check_retrain_conditions()

        if not should_retrain:
            logger.info("\n⏸️ Pipeline pausado - aguardando mais dados")
            return False

        # Passo 3: Preparar dados
        logger.info("\n📋 Passo 3: Preparação de Dados")
        new_examples = self.prepare_training_data()

        if new_examples == 0:
            logger.warning("\n⚠️ Nenhum dado novo para treinar")
            return False

        # Passo 4: Retreinar (se auto_trigger ativado)
        if self.auto_trigger:
            logger.info("\n📋 Passo 4: Retreinamento")
            success = self.trigger_training()

            if success:
                logger.info("\n✅ Pipeline concluído com sucesso!")
                return True
            else:
                logger.error("\n❌ Pipeline falhou no treinamento")
                return False
        else:
            logger.info("\n✅ Dados preparados! Execute manualmente:")
            logger.info("   ./ziva_manager train")
            return True

    def run_continuous(self, check_interval: int = 3600):
        """Executa pipeline continuamente"""
        logger.info(
            f"🔄 Modo contínuo ativado (verificação a cada {check_interval}s)")

        while True:
            try:
                self.run_pipeline()
                logger.info(f"\n⏰ Próxima verificação em {check_interval}s...")
                time.sleep(check_interval)
            except KeyboardInterrupt:
                logger.info("\n⏹️ Pipeline interrompido pelo usuário")
                break
            except Exception as e:
                logger.error(f"\n❌ Erro no pipeline: {e}")
                time.sleep(60)  # Aguardar 1 minuto antes de tentar novamente


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Auto-Retrain Pipeline")
    parser.add_argument(
        '--min-examples',
        type=int,
        default=100,
        help='Mínimo de exemplos novos para retreinar'
    )
    parser.add_argument(
        '--min-quality',
        type=float,
        default=0.8,
        help='Score mínimo de qualidade (0-1)'
    )
    parser.add_argument(
        '--auto-trigger',
        action='store_true',
        help='Disparar treinamento automaticamente'
    )
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Executar continuamente'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=3600,
        help='Intervalo entre verificações (segundos)'
    )

    args = parser.parse_args()

    pipeline = AutoRetrainPipeline(
        min_new_examples=args.min_examples,
        min_quality_score=args.min_quality,
        auto_trigger=args.auto_trigger
    )

    if args.continuous:
        pipeline.run_continuous(check_interval=args.interval)
    else:
        pipeline.run_pipeline()


if __name__ == "__main__":
    main()
