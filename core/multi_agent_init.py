#!/usr/bin/env python3
"""
Multi-Agent System Initializer and Registry.

Registers all specialized agents with the AgentManager and provides
convenient initialization functions.
"""

import logging
from typing import Optional

from core.agent_manager import AgentManager, get_manager
from core.base_agent import ResourceLimits
from agents.coding_agent import CodingAgent
from agents.research_agent import ResearchAgent
from agents.debug_agent import DebugAgent
from agents.planner_agent import PlannerAgent

logger = logging.getLogger("MultiAgentInit")


def initialize_multi_agent_system(
    max_concurrent_agents: int = 3,
    max_ram_gb: float = 24.0,
    max_vram_gb: float = 10.0
) -> AgentManager:
    """
    Initialize the multi-agent system with all specialized agents.

    Args:
        max_concurrent_agents: Maximum concurrent agents
        max_ram_gb: Maximum RAM for agents (GB)
        max_vram_gb: Maximum VRAM for agents (GB)

    Returns:
        AgentManager: Initialized agent manager
    """
    try:
        logger.info("Initializing multi-agent system...")

        # Get or create manager
        manager = get_manager()

        # Register CodingAgent
        manager.register_agent(
            agent_class=CodingAgent,
            role="coding",
            default_resources=ResourceLimits(
                ram_mb=6144,  # 6GB RAM
                vram_mb=5120,  # 5GB VRAM
                cpu_cores=2
            ),
            default_model="deepseek-coder:6.7b",
            description="Code generation and modification specialist"
        )

        # Register ResearchAgent
        manager.register_agent(
            agent_class=ResearchAgent,
            role="research",
            default_resources=ResourceLimits(
                ram_mb=4096,  # 4GB RAM
                vram_mb=2048,  # 2GB VRAM
                cpu_cores=1
            ),
            default_model="llama3.2:3b",
            description="Web search and documentation lookup specialist"
        )

        # Register DebugAgent
        manager.register_agent(
            agent_class=DebugAgent,
            role="debug",
            default_resources=ResourceLimits(
                ram_mb=6144,  # 6GB RAM
                vram_mb=5120,  # 5GB VRAM
                cpu_cores=2
            ),
            default_model="qwen2.5:7b",
            description="Error analysis and testing specialist"
        )

        # Register PlannerAgent
        manager.register_agent(
            agent_class=PlannerAgent,
            role="planner",
            default_resources=ResourceLimits(
                ram_mb=4096,  # 4GB RAM
                vram_mb=2048,  # 2GB VRAM
                cpu_cores=1
            ),
            default_model="llama3.2:3b",
            description="Task decomposition and workflow orchestration"
        )

        # Start maintenance thread
        manager.start_maintenance()

        logger.info("Multi-agent system initialized successfully")
        logger.info(f"Registered agents: {list(manager.agent_specs.keys())}")

        return manager

    except Exception as e:
        logger.error(f"Failed to initialize multi-agent system: {e}")
        raise


def shutdown_multi_agent_system(
        manager: Optional[AgentManager] = None) -> None:
    """
    Shutdown the multi-agent system gracefully.

    Args:
        manager: AgentManager instance (uses singleton if None)
    """
    try:
        if manager is None:
            manager = get_manager()

        logger.info("Shutting down multi-agent system...")
        manager.shutdown()
        logger.info("Multi-agent system shutdown complete")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
