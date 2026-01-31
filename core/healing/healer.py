import logging
import json
import time
from typing import List, Dict, Any, Optional
from core.healing.test_runner import TestRunner, TestResult
from extensions.file_ops import file_reader, file_editor
from core.runtime_client import runtime

logger = logging.getLogger("SelfHealer")

class SelfHealer:
    """
    Orchestrates the Self-Healing process.
    Target -> Test -> Analyze -> Fix -> Verify.
    """

    def __init__(self, max_retries: int = 3):
        self.runner = TestRunner()
        self.max_retries = max_retries

    def heal_file(self, file_path: str, test_command: str = None) -> Dict[str, Any]:
        """
        Attempts to fix bugs in a specific file.
        """
        logger.info(f"🚑 Starting Self-Healing for: {file_path}")
        
        for attempt in range(1, self.max_retries + 1):
            logger.info(f"🔄 Attempt {attempt}/{self.max_retries}")
            
            # 1. Run Tests
            # If no test_command, we just try to run the file itself
            result = self.runner.run_pytest(file_path)
            
            if result.success:
                logger.info(f"✅ Success on attempt {attempt}!")
                return {"success": True, "attempts": attempt, "final_status": "Fixed"}
            
            logger.warning(f"❌ Tests failed. Found {len(result.errors)} errors.")
            
            # 2. Analyze the first error (Priority)
            if not result.errors:
                 logger.error("No structured errors found by parser. Cannot continue automated healing.")
                 return {"success": False, "error": "No structured errors found", "output": result.output}
            
            error = result.errors[-1] # Take the last error (usually the most relevant in Python tracebacks)
            
            # 3. Read the code
            code = file_reader(file_path)
            
            # 4. Use AI to fix it (Simulation for now, or use LLMService if possible)
            # Since I am the agent, I WILL BE the one calling this.
            # But here I implement the 'node' logic.
            
            fix_prompt = f"""
            You are a Self-Healing engine. Fix the following error in the code.
            
            FILE: {file_path}
            ERROR: {error['message']} at line {error['line']}
            
            CODE:
            {code}
            
            Return ONLY the corrected code. No explanations.
            """
            
            try:
                from core.llm import LLMService
                llm = LLMService()
                new_code = llm.completion(fix_prompt, max_tokens=2048)
                
                # Cleanup markdown
                if "```python" in new_code:
                    new_code = new_code.split("```python")[1].split("```")[0].strip()
                elif "```" in new_code:
                    new_code = new_code.split("```")[1].split("```")[0].strip()
                
                # 5. Apply fix
                logger.info(f"🛠️ Applying fix to {file_path}")
                file_editor(file_path, new_code, mode="overwrite")
                
                # Wait a bit before next test
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to generate fix: {e}")
                return {"success": False, "error": str(e)}

        return {"success": False, "error": "Max retries reached"}

