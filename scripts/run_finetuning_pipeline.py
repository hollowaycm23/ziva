"""
Script completo para executar pipeline de fine-tuning da Ziva.

Executa todo o processo:
1. Coleta de dados
2. Criação de datasets
3. Geração de dados sintéticos (teacher-student)
4. Treinamento LoRA/QLoRA
5. Gerenciamento de adaptadores
6. Sincronização P2P
"""

from core.p2p_learning import P2PLearningNode, GabrielleConnector
from core.adapter_manager import AdapterManager
from training.lora_trainer import train_ziva_adapter, ZivaTrainingConfig
from training.teacher_student import TeacherLLM, StudentTrainer
from core.dataset_builder import DatasetBuilder
from core.training_data_collector import TrainingDataCollector
import sys
import logging
from pathlib import Path

# Adicionar ao path
sys.path.insert(0, str(Path(__file__).parent.parent))


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("FineTuningPipeline")


def run_full_pipeline(use_teacher: bool = True,
                      use_p2p: bool = True,
                      task_types: list = None):
    """
    Executa pipeline completo de fine-tuning.

    Args:
        use_teacher (bool): Usar teacher LLM para dados sintéticos
        use_p2p (bool): Sincronizar com peers P2P
        task_types (list): Tipos de tarefas para treinar
    """
    if task_types is None:
        task_types = ['general', 'code-execution', 'web-scraping']

    print("🚀 Iniciando Pipeline de Fine-Tuning da Ziva\n")

    # ========== FASE 1: COLETA DE DADOS ==========
    print("📊 FASE 1: Coleta de Dados")
    collector = TrainingDataCollector()
    count = collector.collect_from_sessions(min_quality=0.7)
    print(f"✅ {count} exemplos coletados das sessões\n")

    # ========== FASE 2: P2P SYNC (OPCIONAL) ==========
    if use_p2p:
        print("🔗 FASE 2: Sincronização P2P")
        gabrielle = GabrielleConnector()

        if gabrielle.is_connected:
            p2p_node = P2PLearningNode(
                node_name="ziva",
                peers=["http://falcon:9000"]
            )
            p2p_node.sync_with_peers()
            print("✅ Conhecimento sincronizado com Gabrielle\n")
        else:
            print("⚠️  Gabrielle não disponível, pulando sincronização\n")

    # ========== FASE 3: GERAÇÃO DE DADOS SINTÉTICOS (OPCIONAL) ==========
    if use_teacher:
        print("🎓 FASE 3: Geração de Dados Sintéticos (Teacher-Student)")

        # Verificar se temos modelo teacher disponível
        teacher = TeacherLLM(provider="ollama", model="qwen2.5-coder:32b")
        trainer = StudentTrainer(teacher)

        tasks = [
            "Executar comandos bash e interpretar resultados",
            "Fazer web scraping com Playwright",
            "Analisar e processar dados em Python",
            "Criar scripts de automação",
            "Integrar com APIs REST"
        ]

        synthetic_path = trainer.create_synthetic_dataset(
            tasks=tasks,
            examples_per_task=20
        )
        print(f"✅ Dataset sintético criado: {synthetic_path}\n")

    # ========== FASE 4: CRIAÇÃO DE DATASETS ==========
    print("📦 FASE 4: Criação de Datasets")
    builder = DatasetBuilder()

    # Dataset geral
    alpaca_count = builder.build_alpaca_dataset(min_quality=0.8)
    print(f"✅ Dataset Alpaca: {alpaca_count} exemplos")

    # Datasets por tarefa
    task_results = builder.build_task_specific_datasets(min_quality=0.8)
    for task, count in task_results.items():
        print(f"  - {task}: {count} exemplos")
    print()

    # ========== FASE 5: TREINAMENTO ==========
    print("🏋️  FASE 5: Treinamento de Adaptadores LoRA/QLoRA")

    adapter_manager = AdapterManager()

    for task_type in task_types:
        dataset_path = f"data/training/tasks/{task_type}_alpaca.json"

        if not Path(dataset_path).exists():
            print(f"⚠️  Dataset não encontrado para {task_type}, pulando...")
            continue

        print(f"\n🎯 Treinando adaptador para: {task_type}")

        try:
            adapter_path = train_ziva_adapter(
                dataset_path=dataset_path,
                task_type=task_type,
                output_dir=f"models/ziva-lora-{task_type}"
            )

            # Registrar adaptador
            adapter_manager.register_adapter(
                adapter_path=adapter_path,
                task_type=task_type,
                version="v1.0",
                metadata={
                    "dataset_size": task_results.get(task_type, 0),
                    "training_date": "2025-12-31"
                }
            )

            print(f"✅ Adaptador treinado e registrado: {task_type}")

        except Exception as e:
            print(f"❌ Erro ao treinar {task_type}: {e}")

    print("\n" + "=" * 60)
    print("✅ PIPELINE COMPLETO!")
    print("=" * 60)

    # Resumo
    print("\n📊 RESUMO:")
    print(f"  - Exemplos coletados: {count}")
    print(f"  - Datasets criados: {len(task_types)}")
    print(f"  - Adaptadores treinados: {len(adapter_manager.list_adapters())}")

    print("\n🎯 PRÓXIMOS PASSOS:")
    print("  1. Testar adaptadores: python scripts/test_adapters.py")
    print("  2. Exportar para Ollama: python scripts/export_to_ollama.py")
    print("  3. Integrar com orquestrador: Adicionar ao start_ziva.py")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Pipeline de Fine-Tuning da Ziva")
    parser.add_argument(
        "--no-teacher",
        action="store_true",
        help="Não usar teacher LLM")
    parser.add_argument(
        "--no-p2p",
        action="store_true",
        help="Não sincronizar P2P")
    parser.add_argument(
        "--tasks",
        nargs="+",
        help="Tipos de tarefas específicas")

    args = parser.parse_args()

    run_full_pipeline(
        use_teacher=not args.no_teacher,
        use_p2p=not args.no_p2p,
        task_types=args.tasks
    )
