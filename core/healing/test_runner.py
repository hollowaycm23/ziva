import logging
import json
import re
import os
from typing import List, Dict, Any, Optional
from extensions.docker_ops import run_docker_container

logger = logging.getLogger("TestRunner")

class TestResult:
    def __init__(self, success: bool, output: str, errors: List[Dict[str, Any]] = None):
        self.success = success
        self.output = output
        self.errors = errors or []

    def to_dict(self):
        return {
            "success": self.success,
            "errors": self.errors,
            "output_snippet": self.output[:500] + "..." if len(self.output) > 500 else self.output
        }

class TestRunner:
    """
    Executes tests inside Docker Containers and parses the results.
    """

    def __init__(self):
        pass

    def run_pytest(self, test_path: str, image: str = "python:3.10-slim") -> TestResult:
        """
        Runs pytest on a specific file or directory inside a container.
        """
        logger.info(f"🧪 Running Pytest on '{test_path}' using {image}...")
        
        # Command to install pytest if missing (or assume image has it? standard python image doesn't)
        # We need a way to ensure deps.
        # For now, let's assume we pip install pytest first or use a prep command.
        # Efficient way: "pip install pytest && pytest file"
        
        # Adjust path for Container Context
        # Host: /path/to/ziva/tmp/foo.py -> Container: /workspace/foo.py
        # We assume input path is relative to project root, e.g. "tmp/foo.py"
        norm_test_path = os.path.normpath(test_path)
        if norm_test_path.startswith("tmp/"):
            container_test_path = norm_test_path[4:] # Strip "tmp/"
        elif norm_test_path.startswith("tmp"):
            container_test_path = norm_test_path[3:].lstrip(os.sep)
        else:
            container_test_path = norm_test_path
        
        cmd = f"pip install -q pytest && pytest {container_test_path}"
        
        output = run_docker_container(
            image=image,
            command=f"bash -c '{cmd}'",
            env="{}",
            allow_network=True 
        )
        
        # Check output for success/failure
        # Pytest execution code is not directly returned by run_docker_container (it returns string output).
        # We parse the text.
        
        if "=== CONTAINER OUTPUT ===" not in output:
             # Runtime/Docker error
             return TestResult(False, output, [{"file": "unknown", "line": 0, "message": "Container failed to run", "raw": output}])

        clean_output = output.replace("=== CONTAINER OUTPUT ===", "").strip()
        
        # Parse Pytest Output
        success = "passed in" in clean_output and "failed" not in clean_output and "ERRORS" not in clean_output
        # Better check: split by "short test summary info"
        
        # Basic Failure Detection
        errors = self._parse_pytest_errors(clean_output)
        
        # If no explicit errors found but output doesn't say passed? 
        # Pytest usually prints "XYZ passed" or "XYZ failed".
        if not success and not errors:
             if "Error" in clean_output or "Traceback" in clean_output:
                 errors.append({"file": "unknown", "line": 0, "message": "Unknown Error detected in output", "raw": clean_output[-1000:]})
        
        # Override success if errors found
        if errors:
            success = False
            
        return TestResult(success, clean_output, errors)

    def _parse_pytest_errors(self, output: str) -> List[Dict[str, Any]]:
        """
        Parses pytest output to extract file, line, and error message.
        """
        errors = []
        
        # Regex for standard pytest failure:
        # path/to/file.py:123: AssertionError
        regex = r"([a-zA-Z0-9_/.-]+\.py):(\d+): (.*)"
        
        for line in output.split('\n'):
            match = re.search(regex, line)
            if match:
                file_path, line_num, msg = match.groups()
                errors.append({
                    "file": file_path,
                    "line": int(line_num),
                    "message": msg.strip()
                })
                
        # Look for SyntaxErrors (Traceback/E style)
        # E     File "/workspace/broken.py", line 7
        
        tb_regex = r'File "([^"]+)", line (\d+).*'
        
        lines = output.split('\n')
        for i, line in enumerate(lines):
            # Strip E prefix if present
            clean_line = line.strip()
            if clean_line.startswith("E "):
                clean_line = clean_line[2:].strip()
                
            match = re.search(tb_regex, clean_line)
            if match:
                file_path = match.group(1)
                line_num = int(match.group(2))
                
                # Check next lines for the Error name
                error_msg = "Unknown Error"
                for j in range(i+1, min(i+5, len(lines))):
                     target_line = lines[j].strip()
                     # If line starts with E, strip and check
                     if target_line.startswith("E "):
                         target_line = target_line[2:].strip()
                         
                     if "Error:" in target_line or "Error" in target_line:
                         error_msg = target_line
                         break
                
                errors.append({
                    "file": file_path,
                    "line": line_num,
                    "message": error_msg
                })

        return errors

