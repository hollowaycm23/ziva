"""
Unified Prompt Optimization System
Integrates both DSPy and Optimus for advanced prompt engineering.
"""

import logging
import os
from typing import Optional, Literal
from enum import Enum

logger = logging.getLogger("PromptOptimizer")


class OptimizerBackend(Enum):
    """Available optimization backends"""
    OPTIMUS = "optimus"
    DSPY = "dspy"
    AUTO = "auto"


class UnifiedPromptOptimizer:
    """
    Unified interface for prompt optimization using multiple backends.
    """

    def __init__(self, backend: OptimizerBackend = OptimizerBackend.AUTO):
        """
        Initialize the unified optimizer.
        """
        self.backend = backend
        self._optimus = None
        self._dspy_available = False

        self._init_optimus()
        self._init_dspy()

        if self.backend == OptimizerBackend.AUTO:
            self.backend = (OptimizerBackend.DSPY if self._dspy_available
                            else OptimizerBackend.OPTIMUS)
            logger.info(f"Auto-selected backend: {self.backend.value}")

    def _init_optimus(self):
        """Initialize Optimus backend"""
        try:
            from core.optimus import PromptOptimizer
            self._optimus = PromptOptimizer()
            logger.info("✅ Optimus backend initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Optimus: {e}")

    def _init_dspy(self):
        """Initialize DSPy backend"""
        try:
            import dspy
            from langchain_ollama import ChatOllama

            model_name = os.getenv("MODEL_NAME", "ziva-base:latest")

            ollama_lm = dspy.LangChainPredict(
                ChatOllama(model=model_name, temperature=0.3)
            )
            dspy.settings.configure(lm=ollama_lm)

            self._dspy_available = True
            logger.info("✅ DSPy backend initialized with Ollama")
        except ImportError:
            logger.info("DSPy not available (not installed)")
        except Exception as e:
            logger.warning(f"Failed to initialize DSPy: {e}")

    def optimize(
        self,
        prompt: str,
        strategy: Literal["general", "code", "creative"] = "general",
        force_backend: Optional[OptimizerBackend] = None
    ) -> str:
        """
        Optimize a prompt using the configured backend.
        """
        backend = force_backend or self.backend

        logger.info(
            f"🔧 Optimizing prompt with {backend.value} ({strategy})")

        if backend == OptimizerBackend.DSPY and self._dspy_available:
            return self._optimize_with_dspy(prompt, strategy)
        elif backend in [OptimizerBackend.OPTIMUS, OptimizerBackend.AUTO]:
            return self._optimize_with_optimus(prompt, strategy)
        else:
            logger.warning(
                f"Backend {backend.value} not available, returning original")
            return prompt

    def _optimize_with_optimus(self, prompt: str, strategy: str) -> str:
        """Optimize using Optimus backend"""
        if not self._optimus:
            logger.warning("Optimus not available, returning original")
            return prompt
        try:
            optimized = self._optimus.optimize(prompt, strategy=strategy)
            logger.info(
                f"✨ Optimus optimization: {len(prompt)} → {len(optimized)} chars")
            return optimized
        except Exception as e:
            logger.error(f"Optimus optimization failed: {e}")
            return prompt

    def _optimize_with_dspy(self, prompt: str, strategy: str) -> str:
        """Optimize using DSPy backend"""
        try:
            import dspy

            class PromptOptimizationSignature(dspy.Signature):
                """Optimize a user prompt to maximize LLM performance."""
                original_prompt = dspy.InputField(desc="The user prompt")
                strategy = dspy.InputField(desc="Optimization strategy")
                optimized_prompt = dspy.OutputField(desc="An optimized version")

            optimizer = dspy.ChainOfThought(PromptOptimizationSignature)
            result = optimizer(original_prompt=prompt, strategy=strategy)
            optimized = result.optimized_prompt
            logger.info(
                f"✨ DSPy optimization: {len(prompt)} → {len(optimized)} chars")
            return optimized
        except Exception as e:
            logger.error(f"DSPy optimization failed: {e}")
            return prompt

    def compare_backends(self, prompt: str, strategy: str = "general") -> dict:
        """
        Compare optimization results from both backends.
        """
        results = {"original": prompt, "original_length": len(prompt),
                   "backends": {}}
        if self._optimus:
            try:
                optimus_result = self._optimize_with_optimus(prompt, strategy)
                results["backends"]["optimus"] = {
                    "prompt": optimus_result, "length": len(optimus_result),
                    "change": len(optimus_result) - len(prompt)}
            except Exception as e:
                logger.error(f"Optimus comparison failed: {e}")
        if self._dspy_available:
            try:
                dspy_result = self._optimize_with_dspy(prompt, strategy)
                results["backends"]["dspy"] = {
                    "prompt": dspy_result, "length": len(dspy_result),
                    "change": len(dspy_result) - len(prompt)}
            except Exception as e:
                logger.error(f"DSPy comparison failed: {e}")
        return results


_optimizer_instance = None


def get_optimizer(
        backend: OptimizerBackend = OptimizerBackend.AUTO
) -> UnifiedPromptOptimizer:
    """Get or create the global optimizer instance"""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = UnifiedPromptOptimizer(backend=backend)
    return _optimizer_instance


if __name__ == "__main__":
    print("🧪 Testing Unified Prompt Optimizer\n")
    optimizer = get_optimizer()
    test_prompt = "write a snake game in python"
    print(f"Original: {test_prompt}\n")
    print("=" * 70)
    optimized = optimizer.optimize(test_prompt, strategy="code")
    print(f"\nOptimized ({optimizer.backend.value}):")
    print(optimized)
    print("\n" + "=" * 70)
    if optimizer._optimus and optimizer._dspy_available:
        print("\n📊 Comparing backends...\n")
        comparison = optimizer.compare_backends(test_prompt, "code")
        for backend_name, result in comparison["backends"].items():
            print(f"\n{backend_name.upper()}:")
            print(f"Length: {result['length']} (change: {result['change']:+d})")
            print(f"Preview: {result['prompt'][:200]}...")