import logging
import json
from typing import List, Dict
from core.llm import LLMService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Optimus")


class PromptOptimizer:
    """
    Experto em Engenharia de Prompt (Meta-Prompting).
    """

    def __init__(self):
        self.llm = LLMService()

    def optimize(self, original_prompt: str, strategy: str = "general") -> str:
        """
        Reescreve o prompt usando técnicas avançadas.
        """
        logger.info(f"🛠️ Optimizing prompt (Strategy: {strategy})...")
        meta_prompt = f"""
        TASK: Act as a World-Class Prompt Engineer.
        Rewrite the following USER PROMPT to be highly effective for a LLM.

        USER PROMPT: "{original_prompt}"

        GUIDELINES:
        - Use clear, direct English.
        - Assign a specific Persona (e.g., "Act as a...").
        - Use delimiters (###) to separate sections.
        - Request "Chain-of-Thought" or step-by-step reasoning if complex.
        - Specify the desired Output Format.

        OUTPUT: Only the rewritten prompt. Do not explain.
        """
        if strategy == "code":
            meta_prompt += "\n- Emphasize clean code and best practices."
        enhanced_prompt = self.llm.completion(meta_prompt)
        return enhanced_prompt.strip()


class SyntheticTeacher:
    """
    Gerador de Dados Sintéticos (Distillation).
    """

    def __init__(self):
        self.llm = LLMService()

    def generate_dataset(self, topic: str, num_samples: int = 5) -> List[Dict]:
        """
        Gera pares de Pergunta/Resposta sobre um tópico.
        """
        logger.info(
            f"📚 Generating data for '{topic}' ({num_samples} samples)...")
        prompt = f"""
        TASK: Generate a synthetic dataset for Fine-Tuning a small LLM.
        TOPIC: {topic}
        COUNT: {num_samples} examples.

        FORMAT: A valid JSON List of objects. Each object must have:
        - "instruction": A user question about the topic.
        - "output": A perfect, concise, and correct answer.

        OUTPUT: Only the JSON list.
        """
        response = self.llm.completion(prompt)
        try:
            clean_resp = response.replace(
                "```json", "").replace(
                "```", "").strip()
            dataset = json.loads(clean_resp)
            logger.info(f"✅ Generated {len(dataset)} examples.")
            return dataset
        except Exception as e:
            logger.error(f"Failed to parse synthetic data: {e}")
            logger.debug(f"Raw Output: {response}")
            return []


if __name__ == "__main__":
    optimus = PromptOptimizer()
    teacher = SyntheticTeacher()
    print("\n--- Test 1: Prompt Optimization ---")
    raw = "write a snake game in python"
    print(f"Original: {raw}")
    print(f"Optimized:\n{optimus.optimize(raw, 'code')}")
    print("\n--- Test 2: Synthetic Data ---")
    data = teacher.generate_dataset("Python List Comprehensions", 2)
    print(json.dumps(data, indent=2))