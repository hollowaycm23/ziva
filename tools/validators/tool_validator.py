import ast
import logging
from typing import List, Tuple

logger = logging.getLogger("ToolValidator")


class ToolValidator:
    """
    Validates Python tool code for security and compliance.
    """

    def __init__(self):
        self.allowed_imports = {
            "math",
            "json",
            "datetime",
            "time",
            "re",
            "random",
            "requests"}
        self.forbidden_functions = {
            "eval",
            "exec",
            "compile",
            "open",
            "input",
            "print",
            "breakpoint",
            "help",
            "exit"}
        self.forbidden_modules = {
            "os",
            "sys",
            "subprocess",
            "shutil",
            "importlib",
            "inspect",
            "socket",
            "urllib"}

    def validate(self, code: str) -> Tuple[bool, List[str]]:
        """
        Parses and validates the Python code.

        Args:
            code: The Python code string to validate.

        Returns:
            A tuple containing (is_valid, list_of_errors).
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, [f"Syntax error: {e}"]

        errors = []

        for node in ast.walk(tree):
            # Check for imports
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    module_name = alias.name.split('.')[0]
                    if module_name not in self.allowed_imports:
                        errors.append(f"Import forbidden: {module_name}")

            # Check for forbidden function calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.forbidden_functions:
                        errors.append(f"Function call forbidden: {node.func.id}")

            # Check for forbidden attributes (e.g., os.system)
            elif isinstance(node, ast.Attribute):
                # Basic check, can be improved to track variable types but
                # that's complex
                if isinstance(
                        node.value,
                        ast.Name) and node.value.id in self.forbidden_modules:
                    errors.append(f"Access to forbidden module attribute: {node.value.id}.{node.attr}")

        # Check loop complexity (simple heuristic: depth of nested loops)
        # This is harder with just AST walk, so omitting for basic version

        return len(errors) == 0, errors
