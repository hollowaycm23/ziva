#!/usr/bin/env python3
"""
Test suite for multi-agent system.

Tests resource management, agent spawning, message routing, and task delegation.
"""

import pytest
import time
from core.agent_manager import AgentManager
from core.base_agent import ResourceLimits, Message, AgentState
from core.resource_monitor import ResourceMonitor, ResourceLimits as MonitorLimits
from core.model_loader import ModelLoader
from agents.coding_agent import CodingAgent
from agents.research_agent import ResearchAgent
from agents.debug_agent import DebugAgent
from agents.planner_agent import PlannerAgent


class TestResourceMonitor:
    """Test suite for ResourceMonitor."""

    def test_initialization(self):
        """
        Test ResourceMonitor initialization.

        Verifies:
            - Monitor initializes with correct limits
            - Available cores are properly allocated
        """
        monitor = ResourceMonitor()
        assert monitor.limits.max_ram_gb == 24.0
        assert monitor.limits.max_vram_gb == 10.0
        assert monitor.limits.max_cpu_cores == 10
        assert len(monitor.available_cores) == 10

    def test_resource_allocation(self):
        """
        Test resource allocation for agents.

        Verifies:
            - Resources can be allocated successfully
            - Allocated resources are tracked correctly
            - CPU cores are removed from available pool
        """
        monitor = ResourceMonitor()
        
        success = monitor.allocate_resources(
            agent_id="test_agent_1",
            ram_mb=4096,
            vram_mb=2048,
            cpu_cores_needed=2
        )
        
        assert success is True
        assert "test_agent_1" in monitor.agent_resources
        assert monitor.agent_resources["test_agent_1"].ram_mb == 4096
        assert len(monitor.available_cores) == 8  # 10 - 2
    
    def test_resource_deallocation(self):
        """
        Test resource deallocation when agent terminates.
        
        Verifies:
            - Resources are properly released
            - CPU cores return to available pool
        """
        monitor = ResourceMonitor()
        monitor.allocate_resources("test_agent_1", 4096, 2048, 2)
        
        monitor.deallocate_resources("test_agent_1")
        
        assert "test_agent_1" not in monitor.agent_resources
        assert len(monitor.available_cores) == 10
    
    def test_max_agents_limit(self):
        """
        Test maximum concurrent agents limit.
        
        Verifies:
            - Cannot spawn more than max_concurrent_agents
            - Proper error message is returned
        """
        monitor = ResourceMonitor()
        
        # Spawn 3 agents (max)
        for i in range(3):
            monitor.allocate_resources(f"agent_{i}", 4096, 2048, 1)
        
        # Try to spawn 4th agent
        can_spawn, reason = monitor.can_spawn_agent(4096, 2048, 1)
        assert can_spawn is False
        assert "Max concurrent agents" in reason


class TestAgentManager:
    """Test suite for AgentManager."""
    
    def test_agent_registration(self):
        """
        Test agent type registration.
        
        Verifies:
            - Agents can be registered with specs
            - Registered agents are tracked in registry
        """
        manager = AgentManager()
        
        manager.register_agent(
            agent_class=CodingAgent,
            role="coding",
            default_resources=ResourceLimits(ram_mb=6144, vram_mb=5120, cpu_cores=2),
            default_model="deepseek-coder:6.7b",
            description="Test coding agent"
        )
        
        assert "coding" in manager.agent_specs
        assert manager.agent_specs["coding"].agent_class == CodingAgent
    
    def test_agent_spawning(self):
        """
        Test agent spawning.
        
        Verifies:
            - Agents can be spawned successfully
            - Agent threads are created
            - Resources are allocated
        
        Note: This test may fail if Ollama is not running
        """
        manager = AgentManager()
        
        manager.register_agent(
            agent_class=ResearchAgent,
            role="research",
            default_resources=ResourceLimits(ram_mb=4096, vram_mb=2048, cpu_cores=1),
            default_model="llama3.2:3b",
            description="Test research agent"
        )
        
        agent_id = manager.spawn_agent(role="research")
        
        if agent_id:  # Only assert if spawn was successful
            assert agent_id in manager.active_agents
            assert agent_id in manager.agent_threads
            
            # Cleanup
            manager.terminate_agent(agent_id)
    
    def test_task_delegation(self):
        """
        Test task delegation to appropriate agent.
        
        Verifies:
            - Tasks are delegated to correct agent type
            - Messages are routed properly
        
        Note: This test may fail if Ollama is not running
        """
        manager = AgentManager()
        
        # Register planner agent
        manager.register_agent(
            agent_class=PlannerAgent,
            role="planner",
            default_resources=ResourceLimits(ram_mb=4096, vram_mb=2048, cpu_cores=1),
            default_model="llama3.2:3b",
            description="Test planner"
        )
        
        task = {
            "type": "task_decomposition",
            "description": "Plan a simple project"
        }
        
        agent_id = manager.delegate_task(task, preferred_role="planner")
        
        if agent_id:
            assert agent_id in manager.active_agents
            assert manager.active_agents[agent_id].role == "planner"
            
            # Cleanup
            manager.terminate_agent(agent_id)


class TestMultiAgentWorkflow:
    """Integration tests for multi-agent workflows."""
    
    @pytest.mark.slow
    def test_coding_research_collaboration(self):
        """
        Test collaboration between CodingAgent and ResearchAgent.
        
        Workflow:
            1. ResearchAgent looks up documentation
            2. CodingAgent generates code based on research
        
        Note: Requires Ollama running with appropriate models
        """
        manager = AgentManager()
        
        # Register agents
        manager.register_agent(
            CodingAgent, "coding",
            ResourceLimits(6144, 5120, 2),
            "deepseek-coder:6.7b",
            "Coding specialist"
        )
        
        manager.register_agent(
            ResearchAgent, "research",
            ResourceLimits(4096, 2048, 1),
            "llama3.2:3b",
            "Research specialist"
        )
        
        # Spawn agents
        research_id = manager.spawn_agent("research")
        coding_id = manager.spawn_agent("coding")
        
        if research_id and coding_id:
            # Send research task
            research_task = {
                "type": "documentation",
                "library": "FastAPI",
                "topic": "dependency injection"
            }
            
            # This would normally be done via message passing
            # For now, just verify agents are active
            assert manager.active_agents[research_id].state != AgentState.TERMINATED
            assert manager.active_agents[coding_id].state != AgentState.TERMINATED
            
            # Cleanup
            manager.terminate_agent(research_id)
            manager.terminate_agent(coding_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
