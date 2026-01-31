#!/usr/bin/env python3
"""
DebugAgent - Specialized agent for error analysis and testing.

Primary responsibilities:
- Error root cause analysis
- Test case generation
- Code validation
- Performance profiling
"""

import logging
from typing import Dict
from core.base_agent import BaseAgent, Message

logger = logging.getLogger("DebugAgent")


class DebugAgent(BaseAgent):
    """
    Specialized agent for debugging tasks.
    
    Uses reasoning-focused LLM (qwen2.5:7b) for deep error analysis.
    """
    
    def __init__(self, agent_id: str, role: str,
                 resource_limits, manager_ref=None):
        """Initialize debug agent with self-healing capabilities."""
        super().__init__(agent_id, role, resource_limits, manager_ref)
        
        self.preferred_tools = [
            "run_tests",
            "analyze_logs",
            "profile_code"
        ]
        
        self._healing_engine = None
        
        logger.info(f"DebugAgent {agent_id} initialized with self-healing")
    
    def process_message(self, message: Message) -> Dict:
        """
        Process debugging task message.
        
        Args:
            message: Incoming message with debug task
        
        Returns:
            dict: Debug analysis results
        """
        logger.info(
            f"DebugAgent {self.agent_id} processing message {message.id}")
        
        content = message.content
        
        if isinstance(content, dict):
            task_type = content.get("type", "error_analysis")
            
            if task_type == "auto_repair":
                return self._auto_repair_workflow(content)
            elif task_type == "error_analysis":
                return self._analyze_error(content)
            elif task_type == "test_generation":
                return self._generate_tests(content)
            elif task_type == "validation":
                return self._validate_code(content)
            else:
                return self._handle_generic_debug(content)
        else:
            return self._handle_generic_debug({"input": str(content)})
    
    def _analyze_error(self, task: Dict) -> Dict:
        """
        Analyze error and find root cause.
        
        Args:
            task: Error analysis task
        
        Returns:
            dict: Root cause analysis
        """
        error_message = task.get("error", "")
        stack_trace = task.get("stack_trace", "")
        code_context = task.get("code", "")
        
        logger.info("Analyzing error")
        
        prompt = f"""Analyze the following error and provide root cause analysis:

Error Message:
{error_message}

Stack Trace:
{stack_trace}

Code Context:
```
{code_context}
```

Provide:
1. Root cause of the error
2. Why it occurred
3. How to fix it
4. Prevention strategies

Analysis:"""
        
        try:
            if not self.model_loaded:
                self.load_model("qwen2.5:7b")
            
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
                analysis = result.get("response", "")
                
                return {
                    "success": True,
                    "analysis": analysis,
                    "agent": self.agent_id
                }
            else:
                return {"success": False, "error": "LLM request failed"}
                
        except Exception as e:
            logger.error(f"Error analyzing error: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_tests(self, task: Dict) -> Dict:
        """
        Generate test cases for code.
        
        Args:
            task: Test generation task
        
        Returns:
            dict: Generated tests
        """
        code = task.get("code", "")
        test_framework = task.get("framework", "pytest")
        
        logger.info(f"Generating {test_framework} tests")
        
        prompt = f"""Generate comprehensive {test_framework} test cases for the
following code:

```
{code}
```

Include:
- Unit tests for all functions
- Edge cases and error handling
- Mock objects where needed
- Assertions for expected behavior

Generate tests:"""
        
        try:
            if not self.model_loaded:
                self.load_model("qwen2.5:7b")
            
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
                tests = result.get("response", "")
                
                if "```" in tests:
                    code_blocks = tests.split("```")
                    if len(code_blocks) >= 3:
                        tests = code_blocks[1]
                        if "\n" in tests:
                            tests = "\n".join(tests.split("\n")[1:])
                
                return {
                    "success": True,
                    "tests": tests.strip(),
                    "framework": test_framework,
                    "agent": self.agent_id
                }
            else:
                return {"success": False, "error": "LLM request failed"}
                
        except Exception as e:
            logger.error(f"Error generating tests: {e}")
            return {"success": False, "error": str(e)}
    
    def _validate_code(self, task: Dict) -> Dict:
        """
        Validate code for correctness.
        
        Args:
            task: Validation task
        
        Returns:
            dict: Validation results
        """
        code = task.get("code", "")
        
        logger.info("Validating code")
        
        prompt = f"""Validate the following code for:
- Syntax errors
- Logic errors
- Type errors
- Potential runtime issues

Code:
```
{code}
```

Validation report:"""
        
        try:
            if not self.model_loaded:
                self.load_model("qwen2.5:7b")
            
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
                validation = result.get("response", "")
                
                return {
                    "success": True,
                    "validation": validation,
                    "agent": self.agent_id
                }
            else:
                return {"success": False, "error": "LLM request failed"}
                
        except Exception as e:
            logger.error(f"Error validating code: {e}")
            return {"success": False, "error": str(e)}
    
    def _handle_generic_debug(self, task: Dict) -> Dict:
        """
        Handle generic debug task.
        
        Args:
            task: Debug task
        
        Returns:
            dict: Debug results
        """
        user_input = task.get("input", str(task))
        
        logger.info("Handling generic debug task")
        
        try:
            if not self.model_loaded:
                self.load_model("qwen2.5:7b")
            
            import requests
            response = requests.post(
                "http://127.0.0.1:11434/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": f"You are an expert debugger. {user_input}",
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
            logger.error(f"Error handling debug task: {e}")
            return {"success": False, "error": str(e)}
    
    @property
    def healing_engine(self):
        """Lazy load self-healing engine."""
        if self._healing_engine is None:
            from core.self_healing_engine import SelfHealingEngine
            self._healing_engine = SelfHealingEngine()
            logger.info("Self-healing engine loaded")
        return self._healing_engine
    
    def _auto_repair_workflow(self, task: Dict) -> Dict:
        """
        Autonomous code repair workflow.
        
        Workflow:
        1. Detect errors in code
        2. Analyze root cause
        3. Generate fixes
        4. Apply and validate
        5. Iterate until success or max attempts
        
        Args:
            task: Auto-repair task with code and options
        
        Returns:
            dict: Repair result
        """
        code = task.get("code", "")
        max_attempts = task.get("max_attempts", 5)
        run_tests = task.get("run_tests", False)
        test_cases = task.get("test_cases")
        
        logger.info(
            f"Starting auto-repair workflow (max_attempts={max_attempts})")
        
        try:
            result = self.healing_engine.repair_code(
                code=code,
                run_tests=run_tests,
                test_cases=test_cases
            )
            
            return {
                "success": result.success,
                "repaired_code": result.repaired_code,
                "errors_fixed": [e.to_dict() for e in result.errors_fixed],
                "attempts_used": len(result.attempts),
                "duration_ms": result.total_duration_ms,
                "rollback_performed": result.rollback_performed,
                "agent": self.agent_id
            }
        
        except Exception as e:
            logger.error(f"Error in auto-repair workflow: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.agent_id
            }