#!/usr/bin/env python3
"""
AgentManager - Central orchestrator for multi-agent system.

Implements AutoGen-inspired patterns:
- Actor model with independent agents
- Message bus for inter-agent communication
- Resource-aware agent spawning and lifecycle management
- Conversation patterns (two-agent, group chat, sequential, handoffs)
"""

import time
import logging
import threading
from typing import Dict, List, Optional, Type, Any
from dataclasses import dataclass

from core.base_agent import BaseAgent, Message, AgentState, ResourceLimits
from core.resource_monitor import get_monitor, ResourceMonitor
from core.model_loader import get_loader, ModelLoader

logger = logging.getLogger("AgentManager")


@dataclass
class AgentSpec:
    """Specification for registering an agent type."""
    agent_class: Type[BaseAgent]
    role: str
    default_resources: ResourceLimits
    default_model: str
    description: str = ""


class AgentManager:
    """
    Central orchestrator for multi-agent system.

    Manages agent lifecycle, resource allocation, and inter-agent communication
    using an actor model with message bus architecture.
    """

    def __init__(
        self,
        max_concurrent_agents: int = 3,
        max_ram_gb: float = 24.0,
        max_vram_gb: float = 10.0
    ):
        """
        Initialize agent manager.

        Args:
            max_concurrent_agents: Max agents active simultaneously
            max_ram_gb: Max RAM available for agents (GB)
            max_vram_gb: Max VRAM available for agents (GB)
        """
        self.max_concurrent_agents = max_concurrent_agents

        self.resource_monitor: ResourceMonitor = get_monitor()
        self.model_loader: ModelLoader = get_loader()

        self.agent_specs: Dict[str, AgentSpec] = {}
        self.active_agents: Dict[str, BaseAgent] = {}
        self.agent_threads: Dict[str, threading.Thread] = {}

        self.message_history: List[Message] = []
        self.routing_lock = threading.Lock()

        self.running = False
        self.maintenance_thread: Optional[threading.Thread] = None

        logger.info(
            f"AgentManager initialized (max agents: {max_concurrent_agents}, "
            f"RAM: {max_ram_gb}GB, VRAM: {max_vram_gb}GB)")

    def register_agent(
        self,
        agent_class: Type[BaseAgent],
        role: str,
        default_resources: ResourceLimits,
        default_model: str,
        description: str = ""
    ):
        """
        Register an agent type.
        """
        spec = AgentSpec(
            agent_class=agent_class,
            role=role,
            default_resources=default_resources,
            default_model=default_model,
            description=description
        )

        self.agent_specs[role] = spec
        logger.info(f"Registered agent type: {role} ({description})")

    def spawn_agent(
        self,
        role: str,
        agent_id: Optional[str] = None,
        custom_resources: Optional[ResourceLimits] = None
    ) -> Optional[str]:
        """
        Spawn a new agent instance.
        """
        if role not in self.agent_specs:
            logger.error(f"Unknown agent role: {role}")
            return None

        spec = self.agent_specs[role]

        if agent_id is None:
            agent_id = f"{role}_{int(time.time() * 1000)}"

        if agent_id in self.active_agents:
            logger.warning(f"Agent {agent_id} already exists")
            return None

        resources = custom_resources or spec.default_resources

        can_spawn, reason = self.resource_monitor.can_spawn_agent(
            resources.ram_mb,
            resources.vram_mb,
            resources.cpu_cores
        )

        if not can_spawn:
            logger.warning(f"Cannot spawn agent {agent_id}: {reason}")
            return None

        success = self.resource_monitor.allocate_resources(
            agent_id,
            resources.ram_mb,
            resources.vram_mb,
            resources.cpu_cores
        )

        if not success:
            logger.error(f"Failed to allocate resources for {agent_id}")
            return None

        try:
            agent = spec.agent_class(
                agent_id=agent_id,
                role=role,
                resource_limits=resources,
                manager_ref=self
            )

            agent.load_model(spec.default_model)
            thread = threading.Thread(target=agent.run, daemon=True)
            thread.start()

            self.active_agents[agent_id] = agent
            self.agent_threads[agent_id] = thread

            logger.info(f"Spawned agent {agent_id} ({role})")
            return agent_id

        except Exception as e:
            logger.error(f"Error spawning agent {agent_id}: {e}")
            self.resource_monitor.deallocate_resources(agent_id)
            return None

    def terminate_agent(self, agent_id: str):
        """
        Terminate an agent.
        """
        if agent_id not in self.active_agents:
            logger.warning(f"Agent {agent_id} not found")
            return

        agent = self.active_agents[agent_id]
        agent.terminate()

        thread = self.agent_threads.get(agent_id)
        if thread:
            thread.join(timeout=5.0)

        self.resource_monitor.deallocate_resources(agent_id)

        del self.active_agents[agent_id]
        if agent_id in self.agent_threads:
            del self.agent_threads[agent_id]

        logger.info(f"Terminated agent {agent_id}")

    def route_message(self, message: Message):
        """
        Route a message to the target agent.
        """
        with self.routing_lock:
            self.message_history.append(message)

            if message.to_agent in self.active_agents:
                target_agent = self.active_agents[message.to_agent]
                target_agent.receive_message(message)
                logger.debug(
                    f"Routed message {message.id} to {message.to_agent}")
            else:
                logger.warning(
                    f"Target agent {message.to_agent} not found, dropped")

    def broadcast(
        self,
        from_agent: str,
        content: Any,
        filter_roles: Optional[List[str]] = None,
        priority: int = 5
    ):
        """
        Broadcast message to all agents.
        """
        for agent_id, agent in self.active_agents.items():
            if agent_id == from_agent:
                continue

            if filter_roles and agent.role not in filter_roles:
                continue

            message = Message(
                id=f"broadcast_{from_agent}_{int(time.time() * 1000)}",
                from_agent=from_agent,
                to_agent=agent_id,
                content=content,
                priority=priority,
                metadata={"broadcast": True}
            )

            self.route_message(message)

        logger.info(
            f"Broadcast from {from_agent} to {len(self.active_agents) - 1} agents")

    def delegate_task(
        self,
        task: Dict,
        preferred_role: Optional[str] = None
    ) -> Optional[str]:
        """
        Delegate a task to an appropriate agent.
        """
        role = preferred_role or self._select_role_for_task(task)

        agent_id = self._find_available_agent(role)
        if not agent_id:
            agent_id = self.spawn_agent(role)

        if not agent_id:
            logger.error(
                f"Failed to delegate task: could not spawn {role} agent")
            return None

        message = Message(
            id=f"task_{int(time.time() * 1000)}",
            from_agent="manager",
            to_agent=agent_id,
            content=task,
            priority=8,
            metadata={"type": "task"}
        )

        self.route_message(message)
        logger.info(f"Delegated task to {agent_id} ({role})")

        return agent_id

    def _select_role_for_task(self, task: Dict) -> str:
        """
        Auto-select appropriate agent role for a task.
        """
        task_str = str(task).lower()
        if any(kw in task_str for kw in [
               "code", "implement", "function", "class", "refactor"]):
            return "coding"
        elif any(kw in task_str for kw in [
                "debug", "error", "fix", "test", "validate"]):
            return "debug"
        elif any(kw in task_str for kw in [
                "search", "research", "documentation", "api"]):
            return "research"
        elif any(kw in task_str for kw in [
                "plan", "design", "architecture", "workflow"]):
            return "planner"
        else:
            return "planner"

    def _find_available_agent(self, role: str) -> Optional[str]:
        """
        Find an available (idle) agent of the specified role.
        """
        for agent_id, agent in self.active_agents.items():
            if agent.role == role and agent.state == AgentState.IDLE:
                return agent_id
        return None

    def get_resource_usage(self) -> Dict:
        """
        Get comprehensive resource usage summary.
        """
        return self.resource_monitor.get_summary()

    def get_agent_status(self, agent_id: str) -> Optional[Dict]:
        """
        Get status of a specific agent.
        """
        if agent_id not in self.active_agents:
            return None
        return self.active_agents[agent_id].get_status()

    def list_agents(self) -> List[Dict]:
        """
        List all active agents.
        """
        return [agent.get_status() for agent in self.active_agents.values()]

    def start_maintenance(self):
        """Start background maintenance tasks."""
        if self.running:
            logger.warning("Maintenance already running")
            return
        self.running = True
        self.maintenance_thread = threading.Thread(
            target=self._maintenance_loop, daemon=True)
        self.maintenance_thread.start()
        logger.info("Started maintenance thread")

    def stop_maintenance(self):
        """Stop background maintenance tasks."""
        self.running = False
        if self.maintenance_thread:
            self.maintenance_thread.join(timeout=5.0)
        logger.info("Stopped maintenance thread")

    def _maintenance_loop(self):
        """Background maintenance loop."""
        while self.running:
            try:
                self.model_loader.check_idle_unload()
                self.model_loader.process_queue()
                for agent_id, agent in list(self.active_agents.items()):
                    if agent.state == AgentState.ERROR:
                        logger.warning(
                            f"Agent {agent_id} in error state, terminating")
                        self.terminate_agent(agent_id)
                time.sleep(5)
            except Exception as e:
                logger.error(f"Error in maintenance loop: {e}")
                time.sleep(10)

    def shutdown(self):
        """Shutdown agent manager and all agents."""
        logger.info("Shutting down AgentManager")
        self.stop_maintenance()
        for agent_id in list(self.active_agents.keys()):
            self.terminate_agent(agent_id)
        logger.info("AgentManager shutdown complete")


_manager_instance: Optional[AgentManager] = None


def get_manager() -> AgentManager:
    """Get or create singleton AgentManager instance."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = AgentManager()
    return _manager_instance