#!/usr/bin/env python3
"""
ResearchAgent - Specialized agent for web search and documentation lookup.

Primary responsibilities:
- Web search and information retrieval
- API documentation lookup
- Library version checking
- Best practices research
"""

import logging
from typing import Dict
from core.base_agent import BaseAgent, Message

logger = logging.getLogger("ResearchAgent")


class ResearchAgent(BaseAgent):
    """
    Specialized agent for research tasks.
    
    Uses lightweight LLM (llama3.2:3b) for fast information retrieval
    and synthesis.
    """
    
    def __init__(self, agent_id: str, role: str, 
                 resource_limits, manager_ref=None):
        """Initialize research agent."""
        super().__init__(agent_id, role, resource_limits, manager_ref)
        
        self.preferred_tools = [
            "web_search",
            "read_documentation",
            "check_package_version"
        ]
        
        logger.info(f"ResearchAgent {agent_id} initialized")
    
    def process_message(self, message: Message) -> Dict:
        """
        Process research task message.
        
        Args:
            message: Incoming message with research task
        
        Returns:
            dict: Research results
        """
        logger.info(
            f"ResearchAgent {self.agent_id} processing message {message.id}"
        )
        
        content = message.content
        
        if isinstance(content, dict):
            task_type = content.get("type", "web_search")
            
            if task_type == "web_search":
                return self._web_search(content)
            elif task_type == "documentation":
                return self._lookup_documentation(content)
            elif task_type == "package_info":
                return self._check_package(content)
            else:
                return self._handle_generic_research(content)
        else:
            return self._handle_generic_research({"query": str(content)})
    
    def _web_search(self, task: Dict) -> Dict:
        """
        Perform web search.
        
        Args:
            task: Search task
        
        Returns:
            dict: Search results
        """
        query = task.get("query", task.get("input", ""))
        
        logger.info(f"Performing web search: {query}")
        
        search_tool = self.tool_manager.get_tool("web_search")
        if search_tool:
            try:
                results = search_tool(query=query)
                return {
                    "success": True,
                    "results": results,
                    "agent": self.agent_id
                }
            except Exception as e:
                logger.error(f"Web search tool failed: {e}")
        
        return self._llm_research(query)
    
    def _lookup_documentation(self, task: Dict) -> Dict:
        """
        Look up API documentation.
        
        Args:
            task: Documentation lookup task
        
        Returns:
            dict: Documentation info
        """
        library = task.get("library", "")
        topic = task.get("topic", "")
        
        logger.info(f"Looking up documentation: {library} - {topic}")
        
        prompt = f"""Provide documentation information for:
Library: {library}
Topic: {topic}

Include:
- Function/class signatures
- Parameters and return types
- Usage examples
- Best practices

Documentation:"""
        
        return self._llm_research(prompt)
    
    def _check_package(self, task: Dict) -> Dict:
        """
        Check package version and information.
        
        Args:
            task: Package check task
        
        Returns:
            dict: Package information
        """
        package = task.get("package", "")
        
        logger.info(f"Checking package: {package}")
        
        try:
            import subprocess
            result = subprocess.run(
                ["pip", "show", package],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "package_info": result.stdout,
                    "agent": self.agent_id
                }
        except Exception as e:
            logger.warning(f"Local package check failed: {e}")
        
        prompt = (f"Provide information about the Python package '{package}', "
                  f"including latest version and key features.")
        return self._llm_research(prompt)
    
    def _handle_generic_research(self, task: Dict) -> Dict:
        """
        Handle generic research query.
        
        Args:
            task: Research task
        
        Returns:
            dict: Research results
        """
        query = task.get("query", task.get("input", str(task)))
        return self._llm_research(query)
    
    def _llm_research(self, query: str) -> Dict:
        """
        Use LLM for research.
        
        Args:
            query: Research query
        
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
                    "prompt": (
                        "You are a research assistant. Provide accurate, "
                        f"concise information.\n\nQuery: {query}\n\nResponse:"
                    ),
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
            logger.error(f"Error in LLM research: {e}")
            return {"success": False, "error": str(e)}