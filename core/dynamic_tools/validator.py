import ast
import logging

logger = logging.getLogger("ToolValidator")

SAFE_BUILTINS = {
    "abs", "all", "any", "ascii", "bin", "bool", "bytearray", "bytes",
    "chr", "complex", "dict", "divmod", "enumerate", "filter", "float",
    "format", "frozenset", "hex", "int", "iter", "len", "list", "map",
    "max", "min", "oct", "ord", "pow", "range", "repr", "reversed",
    "round", "set", "slice", "sorted", "str", "sum", "tuple", "type",
    "zip", "math", "json", "re", "datetime", "collections", "itertools",
    "functools", "typing", "statistics",
}

ALLOWED_IMPORTS = {
    "math", "json", "re", "datetime", "collections", "itertools",
    "functools", "typing", "statistics", "decimal", "random",
    "string", "textwrap", "enum",
}

FORBIDDEN_NAMES = {
    "os", "subprocess", "sys", "shutil", "socket", "requests",
    "urllib", "http", "pathlib", "glob", "shlex", "signal",
    "multiprocessing", "threading", "asyncio", "importlib",
    "pickle", "shelve", "ctypes", "code", "codecs", "io",
    "tempfile", "atexit", "inspect", "platform",
}

FORBIDDEN_ATTRS = {
    "system", "popen", "run", "call", "check_output", "check_call",
    "exec", "eval", "compile", "__import__", "open", "input",
}

FORBIDDEN_CALLS = {"exec", "eval", "compile", "__import__", "open", "input"}


class ValidationError(Exception):
    pass


class ValidationResult:
    def __init__(self, valid: bool, reason: str = "", ast_node=None):
        self.valid = valid
        self.reason = reason
        self.ast_node = ast_node

    def __bool__(self):
        return self.valid


class DynamicToolValidator:
    def __init__(self):
        pass

    def validate(self, code: str) -> ValidationResult:
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return ValidationResult(False, f"Syntax error: {e}")

        has_function_def = False
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                has_function_def = True
                result = self._validate_function(node)
                if not result:
                    return result

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name.split(".")[0]
                    if name in FORBIDDEN_NAMES:
                        return ValidationResult(False, f"Forbidden import: {alias.name}")
                    if name not in ALLOWED_IMPORTS:
                        return ValidationResult(False, f"Import not in allowlist: {alias.name}")

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                base = module.split(".")[0]
                if base in FORBIDDEN_NAMES:
                    return ValidationResult(False, f"Forbidden import from: {module}")
                if base not in ALLOWED_IMPORTS and base:
                    return ValidationResult(False, f"Import source not in allowlist: {module}")

            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
                    return ValidationResult(False, f"Forbidden function call: {node.func.id}()")
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in FORBIDDEN_ATTRS:
                        return ValidationResult(False, f"Forbidden attribute access: {node.func.attr}")

            elif isinstance(node, ast.Attribute):
                if node.attr in FORBIDDEN_ATTRS:
                    return ValidationResult(False, f"Forbidden attribute access: {node.attr}")

        if not has_function_def:
            return ValidationResult(False, "No function definition found")

        return ValidationResult(True)

    def _validate_function(self, node: ast.FunctionDef) -> ValidationResult:
        if not ast.get_docstring(node):
            return ValidationResult(False, "Function must have a docstring")

        if len(node.body) > 50:
            return ValidationResult(False, "Function body too long (max 50 statements)")

        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id in FORBIDDEN_CALLS:
                return ValidationResult(False, f"Forbidden decorator: {decorator.id}")

        return ValidationResult(True)

    @staticmethod
    def get_safe_globals() -> dict:
        return {name: __builtins__[name] for name in SAFE_BUILTINS if name in __builtins__}
