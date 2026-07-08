"""
Prompt Optimization Node for LangGraph Integration
Adds intelligent prompt optimization before LLM generation.
"""

import logging
from typing import TypedDict
from core.prompt_optimizer import get_optimizer, OptimizerBackend
import os

logger = logging.getLogger(__name__)


class PromptOptimizationState(TypedDict):
    """State extension for prompt optimization"""
    original_prompt: str
    optimized_prompt: str
    optimization_applied: bool
    optimization_backend: str


def should_optimize_prompt(state: dict) -> bool:
    """
    Determine if prompt optimization should be applied.
    """
    input_text = state.get("input", "")

    if len(input_text) < 20:
        return False

    greetings = ["olá", "oi", "hello", "hi", "bom dia"]
    if any(g in input_text.lower()
           for g in greetings) and len(input_text.split()) < 5:
        return False

    optimization_keywords = [
        "escreva", "crie", "desenvolva", "implemente", "analise",
        "otimize", "melhore", "refatore", "debugue", "corrija",
        "write", "create", "develop", "implement", "analyze"
    ]

    return any(keyword in input_text.lower()
               for keyword in optimization_keywords)


def prompt_optimization_node(state: dict) -> dict:
    """
    LangGraph node that optimizes prompts before generation.
    """
    from core.auditor import Auditor
    node_name = "prompt_optimization_node"

    try:
        Auditor.log_event(
            "NODE_START", {
                "node": node_name,
                "input_length": len(state.get("input", ""))
            })

        enable_optimization = os.getenv(
            "ENABLE_PROMPT_OPTIMIZATION", "true").lower() == "true"

        if not enable_optimization:
            logger.debug("Prompt optimization disabled via config")
            return {"optimization_applied": False}

        if not should_optimize_prompt(state):
            logger.debug("Skipping optimization for simple query")
            return {"optimization_applied": False}

        backend_name = os.getenv("OPTIMIZATION_BACKEND", "auto")
        backend = OptimizerBackend(
            backend_name) if backend_name != "auto" else OptimizerBackend.AUTO

        optimizer = get_optimizer(backend=backend)

        strategy = "general"
        input_lower = state.get("input", "").lower()

        if any(word in input_lower for word in [
               "código", "code", "python", "javascript", "função"]):
            strategy = "code"
        elif any(
            word in input_lower for word in [
                "criativo", "creative", "história", "story"]):
            strategy = "creative"

        original = state.get("input", "")
        optimized = optimizer.optimize(original, strategy=strategy)

        logger.info(
            f"✨ Prompt optimized: {len(original)} → {len(optimized)} chars "
            f"(backend: {optimizer.backend.value})")

        result = {
            "input": optimized,
            "original_prompt": original,
            "optimized_prompt": optimized,
            "optimization_applied": True,
            "optimization_backend": optimizer.backend.value
        }

        Auditor.log_event("PROMPT_OPTIMIZED", {
            "node": node_name,
            "backend": optimizer.backend.value,
            "strategy": strategy,
            "original_length": len(original),
            "optimized_length": len(optimized),
            "improvement": len(optimized) - len(original)
        })

        Auditor.log_event(
            "NODE_END", {
                "node": node_name, "output": "optimization_applied"})
        return result

    except Exception as e:
        logger.error(f"Prompt optimization failed: {e}")
        Auditor.log_event(
            "NODE_ERROR",
            {"node": node_name, "error": str(e)}, level="ERROR")
        return {"optimization_applied": False}


def add_optimization_to_graph(workflow, optimization_config: dict = None):
    """
    Helper to add prompt optimization node to an existing StateGraph.
    """
    config = optimization_config or {}
    position = config.get("position", "before_analyze")

    workflow.add_node("optimize_prompt", prompt_optimization_node)

    if position == "before_analyze":
        logger.info("Adding prompt optimization before analyze_node")
    elif position == "before_design":
        logger.info("Adding prompt optimization before design_tool_node")
    elif position == "both":
        logger.info("Adding prompt optimization at multiple points")

    return workflow
