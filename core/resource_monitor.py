#!/usr/bin/env python3
"""
ResourceMonitor - Hardware-aware resource tracking for multi-agent system.
"""

import psutil
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger("ResourceMonitor")

try:
    import pynvml
    pynvml.nvmlInit()
    GPU_AVAILABLE = True
    logger.info("GPU monitoring enabled via pynvml")
except Exception as e:
    GPU_AVAILABLE = False
    logger.warning(f"GPU monitoring disabled: {e}")


@dataclass
class ResourceLimits:
    """Resource limits for the multi-agent system."""
    max_ram_gb: float = 24.0
    max_vram_gb: float = 10.0
    max_cpu_cores: int = 10
    max_concurrent_agents: int = 3


@dataclass
class AgentResources:
    """Resource allocation for a single agent."""
    agent_id: str
    ram_mb: int = 0
    vram_mb: int = 0
    cpu_cores: list = None
    model_loaded: Optional[str] = None
    last_active: datetime = None


class ResourceMonitor:
    """
    Real-time hardware resource monitoring and allocation.
    """

    def __init__(self, limits: Optional[ResourceLimits] = None):
        """
        Initialize resource monitor.
        """
        self.limits = limits or ResourceLimits()
        self.agent_resources: Dict[str, AgentResources] = {}
        self.available_cores = list(range(2, 12))

        logger.info(f"ResourceMonitor initialized with limits: "
                    f"RAM={self.limits.max_ram_gb}GB, "
                    f"VRAM={self.limits.max_vram_gb}GB, "
                    f"CPU={self.limits.max_cpu_cores} cores")

    def get_ram_usage(self) -> Dict:
        """
        Get current RAM usage.
        """
        mem = psutil.virtual_memory()
        per_agent = {}
        for agent_id, resources in self.agent_resources.items():
            per_agent[agent_id] = resources.ram_mb / 1024
        return {
            "total_gb": mem.total / (1024**3),
            "used_gb": mem.used / (1024**3),
            "available_gb": mem.available / (1024**3),
            "percent": mem.percent,
            "per_agent": per_agent,
            "agents_total_gb": sum(per_agent.values())
        }

    def get_vram_usage(self) -> Dict:
        """
        Get current GPU VRAM usage.
        """
        if not GPU_AVAILABLE:
            return {
                "total_gb": 0, "used_gb": 0, "available_gb": 0, "percent": 0,
                "loaded_models": [], "error": "GPU monitoring not available"
            }
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            loaded_models = []
            for agent_id, resources in self.agent_resources.items():
                if resources.model_loaded:
                    loaded_models.append({
                        "agent_id": agent_id,
                        "model": resources.model_loaded,
                        "vram_mb": resources.vram_mb
                    })
            return {
                "total_gb": mem_info.total / (1024**3),
                "used_gb": mem_info.used / (1024**3),
                "available_gb": mem_info.free / (1024**3),
                "percent": (mem_info.used / mem_info.total) * 100,
                "loaded_models": loaded_models
            }
        except Exception as e:
            logger.error(f"Error getting VRAM usage: {e}")
            return {
                "total_gb": 0, "used_gb": 0, "available_gb": 0, "percent": 0,
                "loaded_models": [], "error": str(e)
            }

    def get_cpu_usage(self) -> Dict:
        """
        Get current CPU usage.
        """
        per_core = psutil.cpu_percent(interval=0.1, percpu=True)
        per_agent = {}
        for agent_id, resources in self.agent_resources.items():
            if resources.cpu_cores:
                per_agent[agent_id] = {"cores": resources.cpu_cores, "usage": [
                    per_core[c] for c in resources.cpu_cores if c < len(per_core)]}
        return {
            "per_core": per_core,
            "per_agent": per_agent,
            "total_percent": psutil.cpu_percent(interval=0.1)
        }

    def can_spawn_agent(self, ram_mb: int, vram_mb: int,
                        cpu_cores_needed: int) -> tuple[bool, str]:
        """
        Check if resources are available to spawn a new agent.
        """
        active_agents = len(self.agent_resources)
        if active_agents >= self.limits.max_concurrent_agents:
            return False, f"Max concurrent agents ({self.limits.max_concurrent_agents}) reached"
        ram_usage = self.get_ram_usage()
        ram_needed_gb = ram_mb / 1024
        if ram_usage["agents_total_gb"] + ram_needed_gb > self.limits.max_ram_gb:
            return False, "Insufficient RAM"
        vram_usage = self.get_vram_usage()
        vram_needed_gb = vram_mb / 1024
        if GPU_AVAILABLE and vram_usage["used_gb"] + vram_needed_gb > self.limits.max_vram_gb:
            return False, "Insufficient VRAM"
        if len(self.available_cores) < cpu_cores_needed:
            return False, "Insufficient CPU cores"
        return True, "Resources available"

    def allocate_resources(self, agent_id: str, ram_mb: int,
                           vram_mb: int, cpu_cores_needed: int) -> bool:
        """
        Allocate resources to an agent.
        """
        can_spawn, reason = self.can_spawn_agent(
            ram_mb, vram_mb, cpu_cores_needed)
        if not can_spawn:
            logger.warning(
                f"Cannot allocate resources for {agent_id}: {reason}")
            return False
        allocated_cores = self.available_cores[:cpu_cores_needed]
        self.available_cores = self.available_cores[cpu_cores_needed:]
        self.agent_resources[agent_id] = AgentResources(
            agent_id=agent_id,
            ram_mb=ram_mb,
            vram_mb=vram_mb,
            cpu_cores=allocated_cores,
            last_active=datetime.now()
        )
        logger.info(f"Allocated resources for {agent_id}")
        return True

    def deallocate_resources(self, agent_id: str):
        """
        Deallocate resources from a terminated agent.
        """
        if agent_id not in self.agent_resources:
            logger.warning(f"Agent {agent_id} not found in resource registry")
            return
        resources = self.agent_resources[agent_id]
        if resources.cpu_cores:
            self.available_cores.extend(resources.cpu_cores)
            self.available_cores.sort()
        del self.agent_resources[agent_id]
        logger.info(f"Deallocated resources for {agent_id}")

    def update_model_loaded(self, agent_id: str,
                            model_name: Optional[str], vram_mb: int = 0):
        """
        Update the model loaded by an agent.
        """
        if agent_id not in self.agent_resources:
            logger.warning(f"Agent {agent_id} not found in resource registry")
            return
        self.agent_resources[agent_id].model_loaded = model_name
        self.agent_resources[agent_id].vram_mb = vram_mb
        self.agent_resources[agent_id].last_active = datetime.now()
        if model_name:
            logger.info(
                f"Agent {agent_id} loaded model {model_name} ({vram_mb}MB VRAM)")
        else:
            logger.info(f"Agent {agent_id} unloaded model")

    def suggest_agent_to_terminate(self) -> Optional[str]:
        """
        Suggest least active agent for termination.
        """
        if not self.agent_resources:
            return None
        oldest_agent = min(
            self.agent_resources.items(),
            key=lambda x: x[1].last_active or datetime.min
        )
        return oldest_agent[0]

    def get_summary(self) -> Dict:
        """
        Get comprehensive resource usage summary.
        """
        return {
            "ram": self.get_ram_usage(),
            "vram": self.get_vram_usage(),
            "cpu": self.get_cpu_usage(),
            "agents": {
                "active": len(self.agent_resources),
                "max": self.limits.max_concurrent_agents,
                "details": {
                    agent_id: {
                        "ram_mb": res.ram_mb,
                        "vram_mb": res.vram_mb,
                        "cpu_cores": res.cpu_cores,
                        "model_loaded": res.model_loaded,
                        "last_active": res.last_active.isoformat()
                        if res.last_active else None
                    }
                    for agent_id, res in self.agent_resources.items()
                }
            },
            "available_cores": self.available_cores
        }


_monitor_instance: Optional[ResourceMonitor] = None


def get_monitor() -> ResourceMonitor:
    """Get or create singleton ResourceMonitor instance."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = ResourceMonitor()
    return _monitor_instance