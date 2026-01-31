"""
Teacher-Student Learning System for Ziva.

Usa uma LLM "teacher" (maior/melhor) para gerar dados de treinamento
de alta qualidade para a LLM "student" (Ziva).

Técnica conhecida como "Distillation" ou "Self-Instruct".
"""

import logging
import json
import time
from typing import List, Dict, Optional
from pathlib import Path
import requests

logger = logging.getLogger("TeacherStudent")


class TeacherLLM:
    """
    LLM "Teacher" para gerar dados de treinamento.

    Pode usar:
    - GPT-4 (OpenAI)
    - Claude (Anthropic)
    - Gemini (Google)
    - Llama 70B+ (local via Ollama)
    """

    def __init__(self, provider: str = "ollama", model: str = "llama3.1:70b"):
        """
        Inicializa teacher LLM.

        Args:
            provider (str): Provedor (ollama, openai, anthropic)
            model (str): Nome do modelo
        """
        self.provider = provider
        self.model = model

    def generate_training_examples(
            self,
            task_description: str,
            num_examples: int = 10,
            context: Optional[str] = None) -> List[Dict]:
        """
        Gera exemplos de treinamento de alta qualidade.

        Args:
            task_description (str): Descrição da tarefa
            num_examples (int): Número de exemplos a gerar
            context (str, optional): Contexto adicional

        Returns:
            List[Dict]: Exemplos gerados
        """
        prompt = f"""Você é um especialista em criar dados de treinamento para LLMs.

Tarefa: {task_description}

{f'Contexto: {context}' if context else ''}

Gere {num_examples} exemplos de alta qualidade no formato:
{{
  "instruction": "tarefa clara e específica",
  "input": "contexto ou dados de entrada (se aplicável)",
  "output": "resposta ideal e completa"
}}

Requisitos:
1. Instruções devem ser claras e variadas
2. Outputs devem ser corretos e bem formatados
3. Cubra diferentes aspectos da tarefa
4. Inclua casos simples e complexos

Retorne APENAS um array JSON válido com os exemplos.
"""

        response = self._call_llm(prompt)

        try:
            # Extrair JSON da resposta
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                examples = json.loads(json_match.group(0))
                logger.info(f"✅ Gerados {len(examples)} exemplos")
                return examples
        except Exception as e:
            logger.error(f"Erro ao parsear exemplos: {e}")

        return []

    def improve_example(self, example: Dict) -> Dict:
        """
        Melhora um exemplo existente.

        Args:
            example (Dict): Exemplo original

        Returns:
            Dict: Exemplo melhorado
        """
        prompt = f"""Melhore este exemplo de treinamento:

Exemplo original:
{json.dumps(example, indent=2, ensure_ascii=False)}

Melhorias necessárias:
1. Tornar instrução mais clara e específica
2. Adicionar contexto relevante se necessário
3. Melhorar qualidade e completude da resposta
4. Corrigir erros se houver

Retorne o exemplo melhorado em JSON:
"""

        response = self._call_llm(prompt)

        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                improved = json.loads(json_match.group(0))
                return improved
        except BaseException:
            pass

        return example

    def generate_code_examples(self, language: str = "python",
                               task_types: List[str] = None,
                               num_examples: int = 20) -> List[Dict]:
        """
        Gera exemplos específicos de código.

        Args:
            language (str): Linguagem de programação
            task_types (List[str]): Tipos de tarefas
            num_examples (int): Número de exemplos

        Returns:
            List[Dict]: Exemplos de código
        """
        if task_types is None:
            task_types = [
                "web scraping",
                "data processing",
                "file manipulation",
                "API integration",
                "automation scripts"
            ]

        all_examples = []
        examples_per_type = num_examples // len(task_types)

        for task_type in task_types:
            examples = self.generate_training_examples(
                task_description=f"Criar código {language} para {task_type}",
                num_examples=examples_per_type,
                context=f"Código deve ser limpo, bem documentado e seguir boas práticas")
            all_examples.extend(examples)

        return all_examples

    def _call_llm(self, prompt: str) -> str:
        """Chama LLM teacher"""
        if self.provider == "ollama":
            return self._call_ollama(prompt)
        elif self.provider == "openai":
            return self._call_openai(prompt)
        else:
            raise ValueError(f"Provider não suportado: {self.provider}")

    def _call_ollama(self, prompt: str) -> str:
        """Chama Ollama"""
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 2000
                    }
                },
                timeout=120
            )

            if response.status_code == 200:
                return response.json().get("response", "")
        except Exception as e:
            logger.error(f"Erro ao chamar Ollama: {e}")

        return ""

    def _call_openai(self, prompt: str) -> str:
        """Chama OpenAI (requer API key)"""
        # TODO: Implementar se necessário
        pass


class StudentTrainer:
    """
    Treina modelo "student" (Ziva) com dados do teacher.
    """

    def __init__(self, teacher: TeacherLLM):
        """
        Inicializa trainer.

        Args:
            teacher (TeacherLLM): LLM teacher
        """
        self.teacher = teacher

    def create_synthetic_dataset(
            self,
            tasks: List[str],
            examples_per_task: int = 50,
            output_path: str = "data/training/synthetic_dataset.json"):
        """
        Cria dataset sintético de alta qualidade.

        Args:
            tasks (List[str]): Lista de tarefas
            examples_per_task (int): Exemplos por tarefa
            output_path (str): Caminho de saída

        Returns:
            str: Caminho do dataset criado
        """
        logger.info(f"Gerando dataset sintético para {len(tasks)} tarefas...")

        all_examples = []

        for task in tasks:
            logger.info(f"Gerando exemplos para: {task}")
            examples = self.teacher.generate_training_examples(
                task_description=task,
                num_examples=examples_per_task
            )
            all_examples.extend(examples)
            time.sleep(1)  # Rate limiting

        # Salvar
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_examples, f, indent=2, ensure_ascii=False)

        logger.info(
            f"✅ Dataset sintético criado: {output_path} ({
                len(all_examples)} exemplos)")
        return output_path

    def augment_existing_dataset(self, dataset_path: str,
                                 output_path: str):
        """
        Melhora dataset existente usando teacher.

        Args:
            dataset_path (str): Dataset original
            output_path (str): Dataset melhorado
        """
        with open(dataset_path, 'r', encoding='utf-8') as f:
            original_data = json.load(f)

        logger.info(f"Melhorando {len(original_data)} exemplos...")

        improved_data = []
        for i, example in enumerate(original_data):
            if i % 10 == 0:
                logger.info(f"Progresso: {i}/{len(original_data)}")

            improved = self.teacher.improve_example(example)
            improved_data.append(improved)
            time.sleep(0.5)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(improved_data, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Dataset melhorado salvo: {output_path}")


if __name__ == "__main__":
    # Teste
    print("🎓 Teacher-Student Learning System")

    # Inicializar teacher (usar modelo maior se disponível)
    teacher = TeacherLLM(provider="ollama", model="qwen2.5-coder:32b")

    # Criar trainer
    trainer = StudentTrainer(teacher)

    # Tarefas para gerar exemplos
    tasks = [
        "Executar comandos bash e retornar resultados",
        "Fazer web scraping de páginas dinâmicas",
        "Analisar e processar dados em Python",
        "Criar scripts de automação",
        "Integrar com APIs REST"
    ]

    # Gerar dataset sintético
    dataset_path = trainer.create_synthetic_dataset(
        tasks=tasks,
        examples_per_task=20
    )

    print(f"✅ Dataset criado: {dataset_path}")
