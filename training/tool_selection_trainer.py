#!/usr/bin/env python3
"""
Tool Selection Trainer - Teaches Ziva which tool to use in each context.

Creates training data for tool selection and fine-tunes the model.
"""

import json
import logging
from typing import List, Dict
from pathlib import Path


logger = logging.getLogger("ToolSelectionTrainer")


class ToolSelectionTrainer:
    """
    Trains Ziva to select the correct tool based on user queries.
    """

    # Training examples: (query, correct_tool, reasoning)
    TRAINING_EXAMPLES = [
        # Weather queries
        ("qual a temperatura em são paulo", "get_weather",
         "Query sobre temperatura → ferramenta de clima"),
        ("como está o clima hoje", "get_weather",
         "Query sobre clima → ferramenta de clima"),
        ("vai chover amanhã", "get_weather",
         "Query sobre previsão → ferramenta de clima"),
        ("qual o tempo em artur nogueira", "get_weather",
         "Query sobre tempo/clima → ferramenta de clima"),
        ("previsão do tempo para sp", "get_weather",
         "Query sobre previsão → ferramenta de clima"),

        # Date/Time queries
        ("que horas são", "get_datetime",
         "Query sobre hora atual → ferramenta de data/hora"),
        ("qual a data de hoje", "get_datetime",
         "Query sobre data → ferramenta de data/hora"),
        ("que dia é hoje", "get_datetime",
         "Query sobre dia → ferramenta de data/hora"),

        # Web search queries
        ("quem foi albert einstein", "web_search",
         "Query sobre pessoa histórica → busca web"),
        ("o que é python", "web_search",
         "Query sobre conceito/tecnologia → busca web"),
        ("qual anime tem kpop no nome", "web_search",
         "Query sobre anime → busca web"),
        ("que horas geto matou yuta", "web_search",
         "Query sobre evento em anime → busca web"),
        ("quem ganhou o oscar 2024", "web_search",
         "Query sobre evento atual → busca web"),
        ("notícias sobre tecnologia", "web_search",
         "Query sobre notícias → busca web"),

        # Air quality
        ("qualidade do ar em sp", "get_air_quality",
         "Query sobre qualidade do ar → ferramenta específica"),
        ("nível de poluição", "get_air_quality",
         "Query sobre poluição → ferramenta de qualidade do ar"),

        # Calculations
        ("quanto é 2 + 2", "calculate", "Query matemática → ferramenta de cálculo"),
        ("calcule a raiz de 16", "calculate",
         "Query de cálculo → ferramenta matemática"),

        # File operations
        ("leia o arquivo test.txt", "read_file",
         "Query sobre ler arquivo → ferramenta de arquivo"),
        ("crie um arquivo novo.txt", "write_file",
         "Query sobre criar arquivo → ferramenta de escrita"),
    ]

    def __init__(self, output_dir: str = "/home/holloway/ziva/data/training"):
        """
        Initialize trainer.

        Args:
            output_dir: Directory to save training data
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ToolSelectionTrainer initialized (output: {output_dir})")

    def generate_training_data(self) -> List[Dict]:
        """
        Generate training data for tool selection.

        Returns:
            List of training examples
        """
        training_data = []

        for query, tool, reasoning in self.TRAINING_EXAMPLES:
            # Format for fine-tuning
            example = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a tool selection expert. Given a user query, select the most appropriate tool."
                    },
                    {
                        "role": "user",
                        "content": f"Query: {query}\n\nWhich tool should I use?"
                    },
                    {
                        "role": "assistant",
                        "content": json.dumps({
                            "tool": tool,
                            "confidence": 0.95,
                            "reasoning": reasoning
                        })
                    }
                ]
            }
            training_data.append(example)

        logger.info(f"Generated {len(training_data)} training examples")
        return training_data

    def save_training_data(
            self, filename: str = "tool_selection_training.jsonl"):
        """
        Save training data to JSONL file.

        Args:
            filename: Output filename
        """
        training_data = self.generate_training_data()
        output_path = self.output_dir / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            for example in training_data:
                f.write(json.dumps(example, ensure_ascii=False) + '\n')

        logger.info(f"✅ Training data saved: {output_path}")
        logger.info(f"   {len(training_data)} examples")

        return str(output_path)

    def create_pattern_rules(self) -> Dict[str, List[str]]:
        """
        Create pattern matching rules for tool selection.

        Returns:
            Dictionary of tool -> patterns
        """
        rules = {
            "get_weather": [
                "temperatura", "clima", "tempo", "weather", "previsão",
                "chuva", "sol", "nublado", "quente", "frio", "graus"
            ],
            "get_datetime": [
                "hora", "horas", "data", "dia", "hoje", "agora",
                "calendário", "quando", "que dia"
            ],
            "web_search": [
                "quem é", "o que é", "onde fica", "como funciona",
                "pesquise", "busque", "procure", "anime", "filme",
                "notícias", "evento", "história", "celebridade"
            ],
            "get_air_quality": [
                "qualidade do ar", "poluição", "aqi", "ar puro"
            ],
            "calculate": [
                "calcule", "quanto é", "soma", "subtração",
                "multiplicação", "divisão", "raiz", "potência"
            ]
        }

        return rules

    def save_pattern_rules(self, filename: str = "tool_patterns.json"):
        """
        Save pattern rules to JSON file.

        Args:
            filename: Output filename
        """
        rules = self.create_pattern_rules()
        output_path = self.output_dir / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(rules, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Pattern rules saved: {output_path}")
        return str(output_path)

    def train(self):
        """
        Execute complete training workflow.
        """
        logger.info("🎓 Starting tool selection training...")

        # Save training data
        training_path = self.save_training_data()

        # Save pattern rules
        patterns_path = self.save_pattern_rules()

        logger.info("✅ Training complete!")
        logger.info(f"   Training data: {training_path}")
        logger.info(f"   Pattern rules: {patterns_path}")

        return {
            "training_data": training_path,
            "pattern_rules": patterns_path
        }


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    trainer = ToolSelectionTrainer()
    result = trainer.train()

    print("\n" + "=" * 60)
    print("Tool Selection Training Complete!")
    print("=" * 60)
    print(f"Training data: {result['training_data']}")
    print(f"Pattern rules: {result['pattern_rules']}")
    print("=" * 60)
