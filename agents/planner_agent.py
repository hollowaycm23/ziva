#!/usr/bin/env python3
"""
PlannerAgent - Specialized agent for task decomposition and workflow orchestration.

Primary responsibilities:
- Complex task breakdown
- Agent delegation strategy
- Workflow optimization
- Progress tracking
"""

import logging
import time
from typing import Dict, List
from core.base_agent import BaseAgent, Message

logger = logging.getLogger("PlannerAgent")


class PlannerAgent(BaseAgent):
    """
    Specialized agent for planning and orchestration.
    
    Uses lightweight LLM (llama3.2:3b) for fast task decomposition.
    """
    
    def __init__(self, agent_id: str, role: str,
                 resource_limits, manager_ref=None):
        """Initialize planner agent."""
        super().__init__(agent_id, role, resource_limits, manager_ref)
        
        self.active_plans: Dict[str, Dict] = {}
        
        logger.info(f"PlannerAgent {agent_id} initialized")
    
    def process_message(self, message: Message) -> Dict:
        """
        Process planning task message.
        
        Args:
            message: Incoming message with planning task
        
        Returns:
            dict: Execution plan
        """
        logger.info(
            f"PlannerAgent {self.agent_id} processing message {message.id}"
        )
        
        content = message.content
        
        if isinstance(content, dict):
            task_type = content.get("type", "task_decomposition")
            
            if task_type == "task_decomposition":
                return self._decompose_task(content)
            elif task_type == "workflow_design":
                return self._design_workflow(content)
            elif task_type == "agent_delegation":
                return self._delegate_to_agents(content)
            else:
                return self._handle_generic_planning(content)
        else:
            return self._handle_generic_planning({"input": str(content)})
    
    def _decompose_task(self, task: Dict) -> Dict:
        """
        Decompose complex task into subtasks.
        
        Args:
            task: Task to decompose
        
        Returns:
            dict: Decomposed subtasks
        """
        task_description = task.get("description", task.get("input", ""))
        
        logger.info("Decomposing task into subtasks")
        
        prompt = f"""Decompose the following complex task into smaller, 
actionable subtasks:

Task: {task_description}

Provide:
1. List of subtasks in logical order
2. Dependencies between subtasks
3. Estimated complexity for each subtask
4. Recommended agent type for each subtask (coding, research, debug, planner)

Decomposition:"""
        
        try:
            if not self.model_loaded:
                self.load_model("llama3.2:3b")
            
            import requests
            response = requests.post(
                "http://127.0.0.1:11434/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                plan = result.get("response", "")
                
                subtasks = self._parse_plan(plan)
                
                plan_id = f"plan_{int(time.time() * 1000)}"
                self.active_plans[plan_id] = {
                    "original_task": task_description,
                    "subtasks": subtasks,
                    "status": "pending"
                }
                
                return {
                    "success": True,
                    "plan_id": plan_id,
                    "subtasks": subtasks,
                    "plan_text": plan,
                    "agent": self.agent_id
                }
            else:
                return {"success": False, "error": "LLM request failed"}
                
        except Exception as e:
            logger.error(f"Error decomposing task: {e}")
            return {"success": False, "error": str(e)}
    
    def _parse_plan(self, plan_text: str) -> List[Dict]:
        """
        Parse plan text into structured subtasks.
        
        Args:
            plan_text: Raw plan text from LLM
        
        Returns:
            list: Structured subtasks
        """
        subtasks = []
        lines = plan_text.split("\n")
        
        current_task = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line[0].isdigit() and "." in line[:3]:
                if current_task:
                    subtasks.append(current_task)
                
                description = line.split(".", 1)[1].strip() if "." in line else line
                
                agent_type = "coding"
                if any(kw in description.lower()
                       for kw in ["research", "search", "find"]):
                    agent_type = "research"
                elif any(kw in description.lower()
                         for kw in ["debug", "test", "validate"]):
                    agent_type = "debug"
                elif any(kw in description.lower()
                         for kw in ["plan", "design", "organize"]):
                    agent_type = "planner"
                
                current_task = {
                    "description": description,
                    "agent_type": agent_type,
                    "status": "pending"
                }
        
        if current_task:
            subtasks.append(current_task)
        
        return subtasks
    
    def _design_workflow(self, task: Dict) -> Dict:
        """
        Design workflow for task execution.
        
        Args:
            task: Workflow design task
        
        Returns:
            dict: Workflow specification
        """
        requirements = task.get("requirements", "")
        
        logger.info("Designing workflow")
        
        prompt = f"""Design an efficient workflow for the following requirements:

{requirements}

Provide:
1. Workflow steps in sequence
2. Parallel execution opportunities
3. Error handling strategy
4. Success criteria

Workflow design:"""
        
        return self._llm_planning(prompt)
    
    def _delegate_to_agents(self, task: Dict) -> Dict:
        """
        Delegate subtasks to appropriate agents.
        
        Args:
            task: Delegation task
        
        Returns:
            dict: Delegation results
        """
        plan_id = task.get("plan_id")
        
        if not plan_id or plan_id not in self.active_plans:
            return {"success": False, "error": "Invalid plan_id"}
        
        plan = self.active_plans[plan_id]
        subtasks = plan["subtasks"]
        
        logger.info(f"Delegating {len(subtasks)} subtasks to agents")
        
        delegated = []
        for i, subtask in enumerate(subtasks):
            agent_type = subtask["agent_type"]
            
            if self.manager:
                task_msg = {
                    "type": "subtask",
                    "plan_id": plan_id,
                    "subtask_index": i,
                    "description": subtask["description"]
                }
                
                agent_id = self.manager.delegate_task(
                    task_msg, preferred_role=agent_type
                )
                
                if agent_id:
                    delegated.append({
                        "subtask": subtask["description"],
                        "agent_id": agent_id,
                        "agent_type": agent_type
                    })
                    subtask["status"] = "delegated"
                    subtask["assigned_to"] = agent_id
        
        return {
            "success": True,
            "plan_id": plan_id,
            "delegated": delegated,
            "agent": self.agent_id
        }
    
    def _handle_generic_planning(self, task: Dict) -> Dict:
        """
        Handle generic planning task.
        
        Args:
            task: Planning task
        
        Returns:
            dict: Planning results
        """
        user_input = task.get("input", str(task))
        return self._llm_planning(user_input)
    
    def _llm_planning(self, query: str) -> Dict:
        """
        Use LLM for planning.
        
        Args:
            query: Planning query
        
        Returns:
            dict: LLM response
        """
        try:
            if not self.model_loaded:
                self.load_model("llama3.2:3b")
            
            import requests
            
            response = requests.post(
                "http://127.0.0.1:11434/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": f"You are an expert task planner. {query}",
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                output = result.get("response", "")
                
                return {
                    "success": True,
                    "response": output,
                    "agent": self.agent_id
                }
            else:
                return {"success": False, "error": "LLM request failed"}
                
        except Exception as e:
            logger.error(f"Error in LLM planning: {e}")
            return {"success": False, "error": str(e)}