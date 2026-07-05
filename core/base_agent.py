#!/usr/bin/env python3
"""
BaseAgent - Abstract base class for all specialized agents in the multi-agent
system. Implements core agent functionality.
"""

import time
import logging
import queue
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from agent.tools import ToolManager
from core.vector_store import VectorStore
from core.database import DatabaseManager
from core.model_loader import get_loader

logger = logging.getLogger("BaseAgent")


class AgentState(Enum):
    """Agent lifecycle states."""
    IDLE = "idle"
    BUSY = "busy"
    WAITING = "waiting"
    ERROR = "error"
    TERMINATED = "terminated"


@dataclass
class Message:
    """Inter-agent message structure."""
    id: str
    from_agent: str
    to_agent: str
    content: Any
    priority: int = 5
    timestamp: datetime = None
    metadata: Dict = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ResourceLimits:
    """Resource limits for an agent."""
    ram_mb: int
    vram_mb: int
    cpu_cores: int


class BaseAgent(ABC):
    """
    Abstract base class for all specialized agents.
    """

    def __init__(
        self,
        agent_id: str,
        role: str,
        resource_limits: ResourceLimits,
        manager_ref=None
    ):
        """
        Initialize base agent.
        """
        self.agent_id = agent_id
        self.role = role
        self.resource_limits = resource_limits
        self.manager = manager_ref

        self.state = AgentState.IDLE
        self.created_at = datetime.now()
        self.last_active = datetime.now()

        self.inbox = queue.PriorityQueue()
        self.outbox = queue.Queue()

        self.model_name: Optional[str] = None
        self.model_loaded = False

        self._tool_manager = None
        self._vector_store = None
        self._database = None

        logger.info(f"Agent {agent_id} ({role}) initialized with limits: "
                    f"RAM={resource_limits.ram_mb}MB, "
                    f"VRAM={resource_limits.vram_mb}MB, "
                    f"CPU={resource_limits.cpu_cores} cores")

    @property
    def tool_manager(self):
        if self._tool_manager is None:
            self._tool_manager = ToolManager()
            self._tool_manager.load_tools()
        return self._tool_manager

    @property
    def vector_store(self):
        if self._vector_store is None:
            self._vector_store = VectorStore()
        return self._vector_store

    @property
    def database(self):
        if self._database is None:
            self._database = DatabaseManager()
        return self._database

    @abstractmethod
    def process_message(self, message: Message) -> Dict:
        """
        Process an incoming message.
        """
        pass

    def send_message(self, to_agent: str, content: Any,
                     priority: int = 5, metadata: Dict = None) -> str:
        """
        Send message to another agent via AgentManager.
        """
        if not self.manager:
            logger.error(
                f"Agent {self.agent_id} has no manager ref, cannot send")
            return None

        message_id = f"{self.agent_id}_{to_agent}_{int(time.time() * 1000)}"
        message = Message(
            id=message_id,
            from_agent=self.agent_id,
            to_agent=to_agent,
            content=content,
            priority=priority,
            metadata=metadata or {}
        )

        self.outbox.put(message)
        self.manager.route_message(message)

        logger.debug(
            f"Agent {self.agent_id} sent message {message_id} to {to_agent}")
        return message_id

    def receive_message(self, message: Message):
        """
        Receive a message into inbox.
        """
        self.inbox.put((-message.priority, message))
        logger.debug(
            f"Agent {self.agent_id} received message {message.id} "
            f"(priority {message.priority})")

    def request_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Execute a tool from ToolManager.
        """
        tool_func = self.tool_manager.get_tool(tool_name)
        if not tool_func:
            logger.error(f"Tool {tool_name} not found")
            return {"error": f"Tool {tool_name} not found"}

        try:
            logger.info(f"Agent {self.agent_id} executing tool {tool_name}")
            result = tool_func(**kwargs)
            self.last_active = datetime.now()
            return result
        except Exception as e:
            logger.error(f"Tool {tool_name} execution failed: {e}")
            return {"error": str(e)}

    def load_model(self, model_name: str) -> bool:
        loader = get_loader()
        success = loader.load_model(model_name, self.agent_id)
        if success:
            self.model_name = model_name
            self.model_loaded = True
            logger.info(f"Agent {self.agent_id} loaded model {model_name}")
        else:
            logger.error(
                f"Agent {self.agent_id} failed to load model {model_name}")
        return success

    def unload_model(self):
        if not self.model_loaded:
            return
        loader = get_loader()
        loader.unload_model(self.agent_id)

        self.model_name = None
        self.model_loaded = False
        logger.info(f"Agent {self.agent_id} unloaded model")

    def get_memory_usage(self) -> int:
        """
        Get current memory usage of agent process.
        """
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return int(process.memory_info().rss / (1024 * 1024))
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return 0

    def set_state(self, state: AgentState):
        """
        Update agent state.
        """
        old_state = self.state
        self.state = state
        self.last_active = datetime.now()
        logger.debug(
            f"Agent {self.agent_id} state: {old_state.value} → {state.value}")

    def run(self):
        """
        Main agent loop - processes messages from inbox.
        """
        logger.info(f"Agent {self.agent_id} ({self.role}) started")

        while self.state != AgentState.TERMINATED:
            try:
                try:
                    priority, message = self.inbox.get(timeout=1.0)
                    self.set_state(AgentState.BUSY)
                    response = self.process_message(message)
                    if response and message.from_agent:
                        self.send_message(
                            message.from_agent,
                            response,
                            priority=message.priority,
                            metadata={"reply_to": message.id}
                        )
                    self.set_state(AgentState.IDLE)
                except queue.Empty:
                    if self.state == AgentState.BUSY:
                        self.set_state(AgentState.IDLE)
                    time.sleep(0.1)
            except Exception as e:
                logger.error(
                    f"Agent {self.agent_id} error in main loop: {e}")
                self.set_state(AgentState.ERROR)
                time.sleep(1)

        logger.info(f"Agent {self.agent_id} terminated")

    def terminate(self):
        """Terminate agent gracefully."""
        logger.info(f"Terminating agent {self.agent_id}")
        if self.model_loaded:
            self.unload_model()
        self.set_state(AgentState.TERMINATED)

    def get_status(self) -> Dict:
        """
        Get agent status information.
        """
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "state": self.state.value,
            "model_loaded": self.model_name,
            "inbox_size": self.inbox.qsize(),
            "outbox_size": self.outbox.qsize(),
            "memory_usage_mb": self.get_memory_usage(),
            "resource_limits": {
                "ram_mb": self.resource_limits.ram_mb,
                "vram_mb": self.resource_limits.vram_mb,
                "cpu_cores": self.resource_limits.cpu_cores
            },
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat()
        }