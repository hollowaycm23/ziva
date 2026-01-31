#!/usr/bin/env python3
"""
CodingAgent - Specialized agent for code generation and modification.

Primary responsibilities:
- Code generation from specifications
- Code refactoring and optimization
- Documentation generation
- Integration with existing codebase
"""

import logging
from typing import Dict
from core.base_agent import BaseAgent, Message

logger = logging.getLogger("CodingAgent")


class CodingAgent(BaseAgent):
    """
    Specialized agent for coding tasks.
    
    Uses code-specialized LLM (deepseek-coder or qwen2.5-coder) for
    high-quality code generation and modification.
    """

    def __init__(self, agent_id: str, role: str,
                 resource_limits, manager_ref=None):
        """Initialize coding agent."""
        super().__init__(agent_id, role, resource_limits, manager_ref)
        
        self.preferred_tools = [
            "write_file",
            "read_file",
            "execute_code",
            "git_commit",
            "format_code"
        ]
        
        logger.info(f"CodingAgent {agent_id} initialized")
    
    def process_message(self, message: Message) -> Dict:
        """
        Process coding task message.
        
        Args:
            message: Incoming message with coding task
        
        Returns:
            dict: Response with generated code or result
        """
        logger.info(
            f"CodingAgent {self.agent_id} processing message {message.id}"
        )
        
        content = message.content
        
        if isinstance(content, dict):
            task_type = content.get("type", "code_generation")
            
            if task_type == "code_generation":
                return self._generate_code(content)
            elif task_type == "code_refactor":
                return self._refactor_code(content)
            elif task_type == "code_review":
                return self._review_code(content)
            elif task_type == "documentation":
                return self._generate_docs(content)
            else:
                return self._handle_generic_task(content)
        else:
            return self._handle_generic_task({"input": str(content)})
    
    def _generate_code(self, task: Dict) -> Dict:
        """
        Generate code from specification.
        
        Args:
            task: Task specification
        
        Returns:
            dict: Generated code and metadata
        """
        spec = task.get("specification", task.get("input", ""))
        language = task.get("language", "python")
        
        logger.info(f"Generating {language} code from specification")
        
        prompt = f"""You are an expert {language} developer. 
Generate production-ready code based on the following specification:

{spec}

Requirements:
- Follow best practices and design patterns
- Include proper error handling
- Add docstrings and comments
- Ensure code is modular and testable

Generate the code:"""
        
        try:
            if not self.model_loaded:
                self.load_model("deepseek-coder:6.7b")
            
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
                generated_code = result.get("response", "")
                
                if "```" in generated_code:
                    code_blocks = generated_code.split("```")
                    if len(code_blocks) >= 3:
                        generated_code = code_blocks[1]
                        if "\n" in generated_code:
                            generated_code = "\n".join(
                                generated_code.split("\n")[1:]
                            )
                
                return {
                    "success": True,
                    "code": generated_code.strip(),
                    "language": language,
                    "agent": self.agent_id
                }
            else:
                logger.error(f"LLM request failed: {response.status_code}")
                return {"success": False, "error": "LLM request failed"}
                
        except Exception as e:
            logger.error(f"Error generating code: {e}")
            return {"success": False, "error": str(e)}
    
    def _refactor_code(self, task: Dict) -> Dict:
        """
        Refactor existing code.
        
        Args:
            task: Refactoring task
        
        Returns:
            dict: Refactored code
        """
        code = task.get("code", "")
        instructions = task.get(
            "instructions", "Improve code quality and readability"
        )
        
        logger.info("Refactoring code")
        
        prompt = f"""Refactor the following code according to these instructions:

Instructions: {instructions}

Original code:
```
{code}
```

Provide the refactored code with improvements:"""
        
        try:
            if not self.model_loaded:
                self.load_model("deepseek-coder:6.7b")
            
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
                refactored_code = result.get("response", "")
                
                if "```" in refactored_code:
                    code_blocks = refactored_code.split("```")
                    if len(code_blocks) >= 3:
                        refactored_code = code_blocks[1]
                        if "\n" in refactored_code:
                            refactored_code = "\n".join(
                                refactored_code.split("\n")[1:]
                            )
                
                return {
                    "success": True,
                    "code": refactored_code.strip(),
                    "agent": self.agent_id
                }
            else:
                return {"success": False, "error": "LLM request failed"}
                
        except Exception as e:
            logger.error(f"Error refactoring code: {e}")
            return {"success": False, "error": str(e)}
    
    def _review_code(self, task: Dict) -> Dict:
        """
        Review code for issues and improvements.
        
        Args:
            task: Code review task
        
        Returns:
            dict: Review feedback
        """
        code = task.get("code", "")
        
        logger.info("Reviewing code")
        
        prompt = f"""Review the following code and provide feedback on:
- Potential bugs or errors
- Code quality and best practices
- Performance optimizations
- Security concerns

Code to review:
```
{code}
```

Provide detailed review feedback:"""
        
        try:
            if not self.model_loaded:
                self.load_model("qwen2.5-coder:7b")
            
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
                feedback = result.get("response", "")
                
                return {
                    "success": True,
                    "feedback": feedback,
                    "agent": self.agent_id
                }
            else:
                return {"success": False, "error": "LLM request failed"}
                
        except Exception as e:
            logger.error(f"Error reviewing code: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_docs(self, task: Dict) -> Dict:
        """
        Generate documentation for code.
        
        Args:
            task: Documentation task
        
        Returns:
            dict: Generated documentation
        """
        code = task.get("code", "")
        doc_type = task.get("doc_type", "docstrings")
        
        logger.info(f"Generating {doc_type} documentation")
        
        prompt = f"""Generate {doc_type} documentation for the following code:

```
{code}
```

Provide comprehensive documentation:"""
        
        try:
            if not self.model_loaded:
                self.load_model("deepseek-coder:6.7b")
            
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
                documentation = result.get("response", "")
                
                return {
                    "success": True,
                    "documentation": documentation,
                    "agent": self.agent_id
                }
            else:
                return {"success": False, "error": "LLM request failed"}
                
        except Exception as e:
            logger.error(f"Error generating documentation: {e}")
            return {"success": False, "error": str(e)}
    
    def _handle_generic_task(self, task: Dict) -> Dict:
        """
        Handle generic coding task.
        
        Args:
            task: Generic task
        
        Returns:
            dict: Task result
        """
        user_input = task.get("input", str(task))
        
        logger.info("Handling generic coding task")
        
        try:
            if not self.model_loaded:
                self.load_model("deepseek-coder:6.7b")
            
            import requests
            response = requests.post(
                "http://127.0.0.1:11434/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": f"You are an expert developer. {user_input}",
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
            logger.error(f"Error handling task: {e}")
            return {"success": False, "error": str(e)}