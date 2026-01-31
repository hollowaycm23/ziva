import logging
from typing import Optional, Tuple

from core.interpreter import SafeInterpreter
from core.llm import LLMService
import re

logger = logging.getLogger("System2")


class System2Thinking:
    """
    Implements 'System 2' thinking (Slow, Deliberate) for complex tasks.
    Generates a hidden Chain-of-Thought before producing the final answer.
    """

    def __init__(self, model_name: str = "ziva-base:latest"):
        self.llm = LLMService(model=model_name)
        self.interpreter = SafeInterpreter()

    def think_and_solve(self, user_query: str) -> Tuple[str, str]:
        """
        Executes the two-step thinking process.
        """
        logger.info(f"🐢 System 2 Activated for: '{user_query[:30]}...'")
        rationale = self._generate_rationale(user_query)
        code_blocks = re.findall(r"```python(.*?)```", rationale, re.DOTALL)
        execution_results = ""

        if code_blocks:
            logger.info("🧮 Code detected in rationale. Executing...")
            for i, code in enumerate(code_blocks):
                result = self.interpreter.execute(code.strip())
                execution_results += (f"\n[Code Execution Result #{i + 1}]: "
                                      f"{result}\n")
            rationale += f"\n\n--- INTERPRETER OUTPUT ---\n{execution_results}"
            logger.info(f"Output: {execution_results.strip()}")
        final_answer = self._generate_final_answer(user_query, rationale)
        return rationale, final_answer

    def _generate_rationale(self, query: str) -> str:
        """
        Generates the hidden Chain-of-Thought.
        """
        prompt = f"""
        User Query: "{query}"

        TASK: Perform a deep, step-by-step analysis of this query.
        - If the problem involves Math, Logic, or Data Processing,
          YOU MUST WRITE PYTHON CODE to solve it.
        - Enclose the Python code in ```python blocks.
        - The code should print() the final answer.
        - Do not guess the answer if you can calculate it.

        OUTPUT FORMAT: Reasoning + Code Blocks.
        """
        logger.info("🤔 Generating Rationale...")
        response = self.llm.completion(prompt)
        return response.strip()

    def _generate_final_answer(self, query: str, rationale: str) -> str:
        """
        Generates the refined final response using the rationale.
        """
        prompt = f"""
        User Query: "{query}"

        My Internal Reasoning (Draft):
        {rationale}

        TASK: tailored the final response to the user based on the reasoning
        above. Be concise and direct. Do not explicitly mention "Internal
        Reasoning" or "Draft". Provide the correct answer/solution clearly.
        """
        logger.info("✨ Generating Final Answer...")
        response = self.llm.completion(prompt)
        return response.strip()


if __name__ == "__main__":
    sys2 = System2Thinking()
    q = "If I have 3 apples and you take 2, but then give me 1 back, how many do I have?"
    rate, ans = sys2.think_and_solve(q)
    print(f"\n🧠 Rationale:\n{rate}\n")
    print(f"🗣️ Answer:\n{ans}")