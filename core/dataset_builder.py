"""
Dataset Builder for Ziva Fine-Tuning.

Converte dados de treinamento em formatos otimizados para LoRA/QLoRA.
"""

import json
import logging
from typing import Dict, Optional
from pathlib import Path
from core.training_data_collector import TrainingDataCollector

logger = logging.getLogger("DatasetBuilder")


class DatasetBuilder:
    """
    Constrói datasets otimizados para fine-tuning.
    """

    def __init__(self, collector: TrainingDataCollector = None):
        """
        Inicializa o builder.
        """
        self.collector = collector or TrainingDataCollector()

    def build_alpaca_dataset(
            self,
            task_type: Optional[str] = None,
            min_quality: float = 0.8,
            output_path: str = "data/training/alpaca_dataset.json") -> int:
        """
        Cria dataset no formato Alpaca.
        """
        raw_data = self.collector.get_training_dataset(
            task_type=task_type,
            min_quality=min_quality
        )

        alpaca_data = []
        for item in raw_data:
            alpaca_data.append({
                "instruction": item['instruction'],
                "input": item.get('input', ''),
                "output": item['output']
            })

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(alpaca_data, f, indent=2, ensure_ascii=False)

        logger.info(
            f"Dataset Alpaca criado: {output_path} ({len(alpaca_data)} exs)")
        return len(alpaca_data)

    def build_sharegpt_dataset(
            self,
            task_type: Optional[str] = None,
            min_quality: float = 0.8,
            output_path: str = "data/training/sharegpt_dataset.json") -> int:
        """
        Cria dataset no formato ShareGPT.
        """
        raw_data = self.collector.get_training_dataset(
            task_type=task_type,
            min_quality=min_quality
        )

        sharegpt_data = []
        for item in raw_data:
            conversation = {
                "conversations": [
                    {
                        "from": "human",
                        "value": item['instruction']
                    },
                    {
                        "from": "gpt",
                        "value": item['output']
                    }
                ]
            }
            sharegpt_data.append(conversation)

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sharegpt_data, f, indent=2, ensure_ascii=False)

        logger.info(
            f"Dataset ShareGPT criado: {output_path} ({len(sharegpt_data)} exs)")
        return len(sharegpt_data)

    def build_task_specific_datasets(self, min_quality: float = 0.8,
                                     output_dir: str = "data/training/tasks"
                                     ) -> Dict[str, int]:
        """
        Cria datasets separados por tipo de tarefa.
        """
        task_types = [
            'code-execution', 'web-scraping', 'information-retrieval',
            'code-generation', 'general'
        ]

        results = {}
        for task_type in task_types:
            output_path = f"{output_dir}/{task_type}_alpaca.json"
            count = self.build_alpaca_dataset(
                task_type=task_type,
                min_quality=min_quality,
                output_path=output_path
            )
            results[task_type] = count

        return results

    def create_train_val_split(self, dataset_path: str,
                               val_ratio: float = 0.1,
                               output_dir: Optional[str] = None) -> tuple:
        """
        Divide dataset em treino e validação.
        """
        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        import random
        random.shuffle(data)

        val_size = int(len(data) * val_ratio)
        train_data = data[val_size:]
        val_data = data[:val_size]

        if output_dir is None:
            output_dir = Path(dataset_path).parent

        train_path = f"{output_dir}/train_dataset.json"
        val_path = f"{output_dir}/val_dataset.json"

        with open(train_path, 'w', encoding='utf-8') as f:
            json.dump(train_data, f, indent=2, ensure_ascii=False)

        with open(val_path, 'w', encoding='utf-8') as f:
            json.dump(val_data, f, indent=2, ensure_ascii=False)

        logger.info(
            f"Split: {len(train_data)} treino, {len(val_data)} validação")
        return train_path, val_path, len(train_data), len(val_data)

    def augment_dataset(self, dataset_path: str,
                        output_path: str,
                        augmentation_factor: int = 2) -> int:
        """
        Aumenta dataset com variações.
        """
        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        augmented = list(data)

        for item in data:
            for _ in range(augmentation_factor - 1):
                variant = item.copy()
                if 'instruction' in variant:
                    variant['instruction'] = self._add_variation(
                        variant['instruction'])
                augmented.append(variant)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(augmented, f, indent=2, ensure_ascii=False)

        logger.info(
            f"Dataset aumentado: {len(data)} -> {len(augmented)} exemplos")
        return len(augmented)

    def _add_variation(self, instruction: str) -> str:
        """Adiciona pequena variação à instrução"""
        variations = [
            f"Por favor, {instruction.lower()}",
            f"{instruction}.",
            instruction.capitalize(),
            f"Preciso que você {instruction.lower()}"
        ]
        import random
        return random.choice(variations)


if __name__ == "__main__":
    builder = DatasetBuilder()
    print("📊 Coletando dados de treinamento...")
    collector = TrainingDataCollector()
    count = collector.collect_from_sessions(min_quality=0.7)
    print(f"✅ {count} exemplos coletados")
    print("\n📦 Criando datasets...")
    alpaca_count = builder.build_alpaca_dataset(min_quality=0.8)
    print(f"✅ Dataset Alpaca: {alpaca_count} exemplos")
    sharegpt_count = builder.build_sharegpt_dataset(min_quality=0.8)
    print(f"✅ Dataset ShareGPT: {sharegpt_count} exemplos")
    print("\n🎯 Criando datasets por tarefa...")
    task_results = builder.build_task_specific_datasets(min_quality=0.8)
    for task, count in task_results.items():
        print(f"  - {task}: {count} exemplos")